# coding=utf-8
# Copyright 2020 The TensorFlow Datasets Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""API utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from typing import Any
from typing import Callable
from typing import Iterable
from typing import List
from typing import overload
from typing import Optional
from typing import Sized
from typing import Union

import functools
import inspect

import six
import wrapt


__all__ = [
    "disallow_positional_args"
]

REQUIRED_ARG = object()
_POSITIONAL_ARG_ERR_MSG = (
    "Please use keyword arguments and not positional arguments. This enables "
    "more flexible API development. Thank you!\n"
    "Positional arguments passed to fn %s: %s.")

FNT = TypeVar('FNT')

# pytype: disable=pointless-statement
# pylint: disable=unused-argument
@overload
def disallow_positional_args(wrapped: None,
                             allowed: List[str]) -> Callable[[FNT], FNT]:
  ...

@overload
def disallow_positional_args(wrapped: FNT, allowed: None) -> FNT:
  ...

def disallow_positional_args(wrapped=None, allowed=None):
  """Requires function to be called using keyword arguments."""
  # See
  # https://wrapt.readthedocs.io/en/latest/decorators.html#decorators-with-optional-arguments
  # for decorator pattern.
  if wrapped is None:
    return functools.partial(disallow_positional_args, allowed=allowed)

  @wrapt.decorator
  def disallow_positional_args_dec(fn: Callable[[], Any],
                                   instance: Optional[object],
                                   args: Sized, kwargs: Iterable) -> object:
    ismethod = instance is not None
    _check_no_positional(fn, args, ismethod, allowed=allowed)
    _check_required(fn, kwargs)
    return fn(*args, **kwargs)

  return disallow_positional_args_dec(wrapped)  # pylint: disable=no-value-for-parameter
# pylint: enable=unused-argument
# pytype: enable=pointless-statement


def _check_no_positional(fn: Callable[[], Any],
                         args: Sized,
                         is_method: bool = False,
                         allowed: Optional[object] = None) -> None:
  """Method is to check for availability of positional args."""
  allowed = set(allowed or [])
  offset = int(is_method)
  if args:
    arg_names = getargspec(fn).args[offset:offset + len(args)]
    if all([name in allowed for name in arg_names]):
      return
    raise ValueError(_POSITIONAL_ARG_ERR_MSG % (fn.__name__, str(arg_names)))


def _required_args(fn: Callable[..., Any]) -> List[str]:
  """Returns arguments of fn with default=REQUIRED_ARG."""
  spec = getargspec(fn)
  if not spec.defaults:
    return []

  arg_names = spec.args[-len(spec.defaults):]
  return [name for name, val in zip(arg_names, spec.defaults)
          if val is REQUIRED_ARG]


def _check_required(fn: Callable[[], Any], kwargs: Iterable) -> None:
  required_args = _required_args(fn)
  for arg in required_args:
    if arg not in kwargs:
      raise ValueError("Argument %s is required." % arg)


def getargspec(
    fn: Callable[[], Any]
    ) -> Union[inspect.FullArgSpec, inspect.ArgSpec]:
  if six.PY3:
    spec = inspect.getfullargspec(fn)
  else:
    spec = inspect.getargspec(fn)  # pylint: disable=deprecated-method
  return spec
