#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from functools import update_wrapper
from functools import wraps


def disable(func):
    '''
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    >>> memo = disable

    '''
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result

    return wrapper


def decorator(dec):
    '''
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    '''
    def wrapper(func):
        return update_wrapper(dec(func), func)

    return wrapper


@decorator
def countcalls(func):
    '''Decorator that counts calls made to the function decorated.'''
    def wrapper(*args, **kwargs):
        wrapper.calls += 1
        #print("cc_wrapper: " + repr(wrapper.__dict__) + " " + repr(wrapper.__name__))
        return func(*args, **kwargs)

    wrapper.calls = 0
    return wrapper


@decorator
def memo(func):
    '''
    Memoize a function so that it caches all return values for
    faster future lookups.
    '''
    def wrapper(*args, **kwargs):
        update_wrapper(wrapper, func)

        key = (args, tuple(sorted(kwargs.items())))

        if key in wrapper.cache:
            result = wrapper.cache[key]
        else:
            result = func(*args, **kwargs)
            wrapper.cache[key] = result

        #result = wrapper.cache.setdefault(key, func(*args, **kwargs))
        #print("memo_wrapper: " + repr(wrapper.__dict__))
        return result

    wrapper.cache = {}
    return wrapper


@decorator
def n_ary(func):
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''
    def wrapper(*args, **kwargs):
        #print("n_ary_wrapper: " + repr(wrapper.__dict__))

        if len(args) > 2:
            return wrapper(args[0], wrapper(*args[1:], **kwargs), **kwargs)
        else:
            res = func(*args, **kwargs)
            return res

    return wrapper


def trace(marker):
    '''Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    >>> fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    '''
    @decorator
    def tracer(func):
        def wrapper(*args, **kwargs):
            print("{} --> {}({})".format(marker*wrapper.counter, wrapper.__name__, args[0]))
            wrapper.counter += 1
            res = func(*args, **kwargs)
            wrapper.counter -= 1
            print("{} <-- {}({}) == {}".format(marker*wrapper.counter, wrapper.__name__, args[0], res))
            return res

        wrapper.counter = 0
        return wrapper

    return tracer


#memo = disable

@memo
@countcalls
@n_ary
def foo(a, b):
    """Fooo"""
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@trace("____")
@memo
def fib(n):
    """Some doc"""
    return 1 if n <= 1 else fib(n-1) + fib(n-2)


def main():
    print(foo(4, 3))
    print(foo(4, 3, 2))
    print(foo(5, 4, 3, 2, 1))

    print(foo(4, 3))
    print(foo(4, 3, 2))
    print(foo(5, 4, 3, 2, 1))

    print("foo was called", foo.calls, "times")

    print(bar(4, 3))
    print(bar(4, 3, 2))
    print(bar(4, 3, 2, 1))
    print("bar was called", bar.calls, "times")

    print(fib.__doc__)
    fib(3)
    print(fib.calls, 'calls made')


if __name__ == '__main__':
    main()
