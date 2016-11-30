#!/usr/bin/env python

import lollipop.types as lt
import lollipop.validators as lv
from collections import namedtuple

import timeit
import os
import hotshot, hotshot.stats


def profile(func, *args, **kwargs):
    prof = hotshot.Profile("object.prof")
    prof.runcall(func, *args, **kwargs)
    prof.close()
    stats = hotshot.stats.load("object.prof")
    stats.strip_dirs()
    stats.sort_stats('time', 'calls')
    stats.print_stats(30)
    os.remove('object.prof')


def benchmark_large_strings_object_dumping(iterations=1000):
    n = 100
    TYPE = lt.Object({
        'field%02d' % idx: lt.String()
        for idx in xrange(n)
    })

    Data = namedtuple('Data', ['field%02d' % idx for idx in xrange(n)])
    data = Data(*['value%02d' % idx for idx in xrange(n)])

    TYPE.dump(data)  # warmup
    time = timeit.timeit(lambda: TYPE.dump(data), number=iterations)
    print 'Large strings object dumping: %s' % time


def benchmark_large_strings_object_loading(iterations=1000):
    n = 100
    TYPE = lt.Object({
        'field%02d' % idx: lt.String()
        for idx in xrange(n)
    })

    data = {'field%02d' % idx: 'value%02d' % idx for idx in xrange(n)}

    TYPE.load(data)  # warmup
    time = timeit.timeit(lambda: TYPE.load(data), number=iterations)
    print 'Large strings object loading: %s' % time


def benchmark_large_strings_object_with_validators_loading(iterations=1000):
    n = 100
    TYPE = lt.Object({
        'field%02d' % idx: lt.String(validate=lv.Length(min=1))
        for idx in xrange(n)
    })

    data = {'field%02d' % idx: 'value%02d' % idx for idx in xrange(n)}

    TYPE.load(data)  # warmup
    time = timeit.timeit(lambda: TYPE.load(data), number=iterations)
    print 'Large strings object with validators loading: %s' % time


def benchmark_large_integers_object_dumping(iterations=1000):
    n = 100
    TYPE = lt.Object({
        'field%02d' % idx: lt.Integer()
        for idx in xrange(n)
    })

    Data = namedtuple('Data', ['field%02d' % idx for idx in xrange(n)])
    data = Data(*[idx for idx in xrange(n)])

    TYPE.dump(data)  # warmup
    time = timeit.timeit(lambda: TYPE.dump(data), number=iterations)
    print 'Large integers object dumping: %s' % time


def benchmark_large_integers_object_loading(iterations=1000):
    n = 100
    TYPE = lt.Object({
        'field%02d' % idx: lt.Integer()
        for idx in xrange(n)
    })

    data = {'field%02d' % idx: idx for idx in xrange(n)}

    TYPE.load(data)  # warmup
    time = timeit.timeit(lambda: TYPE.load(data), number=iterations)
    print 'Large integers object loading: %s' % time


def benchmark_complex_object_dumping(iterations=1000):
    Foo = namedtuple('Foo', ['a', 'b', 'c', 'd'])
    Bar = namedtuple('Bar', ['x', 'y', 'foo', 'foos'])

    FOO = lt.Object({
        'a': lt.Integer(),
        'b': lt.FunctionField(lt.Integer(), lambda o: o.b + 10),
        'c': lt.String(),
        'd': lt.Integer(),
    })

    BAR = lt.Object({
        'x': lt.String(),
        'y': lt.Integer(),
        'foo': FOO,
        'foos': lt.List(FOO),
    })

    bar = Bar(
        'bar', 123,
        Foo(123, 456, 'foo', 789),
        [Foo(123+i, 456+i, 'foo', 789+i) for i in xrange(10)]
    )

    BAR.dump(bar)  # warmup
    time = timeit.timeit(lambda: BAR.dump(bar), number=iterations)
    print 'Complex object dumping: %s' % time


def benchmark_complex_object_loading(iterations=1000):
    Foo = namedtuple('Foo', ['a', 'b', 'c', 'd'])
    Bar = namedtuple('Bar', ['x', 'y', 'foo', 'foos'])

    FOO = lt.Object({
        'a': lt.Integer(),
        'b': lt.FunctionField(lt.Integer(), lambda o: o.b + 10),
        'c': lt.String(),
        'd': lt.Integer(),
    })

    BAR = lt.Object({
        'x': lt.String(),
        'y': lt.Integer(),
        'foo': FOO,
        'foos': lt.List(FOO),
    })

    data = {
        'x': 'bar', 'y': 123,
        'foo': {'a': 123, 'b': 456, 'c': 'foo', 'd': 789},
        'foos': [{'a': 123+i, 'b': 456+i, 'c': 'foo', 'd': 789+i}
                 for i in xrange(10)],
    }

    BAR.load(data)  # warmup
    time = timeit.timeit(lambda: BAR.load(data), number=iterations)
    print 'Complex object loading: %s' % time


benchmark_large_strings_object_dumping()
benchmark_large_integers_object_dumping()
benchmark_complex_object_dumping()
benchmark_large_strings_object_loading()
benchmark_large_integers_object_loading()
benchmark_large_strings_object_with_validators_loading()
benchmark_complex_object_loading()
