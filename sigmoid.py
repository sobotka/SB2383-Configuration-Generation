#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sigmoid and curve utilities.

Functions related to the generation of sigmoid curves etc.

__author__ = Troy James Sobotka
__copyright__ = Copyright 2023
__version__ = 1.0
__maintainer__ = Troy James Sobotka
__email__ = troy.sobotka@gmail.com
__status__ = Test
"""

import numpy


# This module is entirely based on Jed Smith's amazing tunable sigmoid. Originating
# math located at https://www.desmos.com/calculator/yrysofmx8h. Python port by
# yours truly.
def equation_scale(x_pivot, y_pivot, slope_pivot, power):
    x_pivot = numpy.asarray(x_pivot)
    y_pivot = numpy.asarray(y_pivot)
    slope_pivot = numpy.asarray(slope_pivot)
    power = numpy.asarray(power)

    return (
        ((slope_pivot * x_pivot) ** -power)
        * (((slope_pivot * (x_pivot / y_pivot)) ** power) - 1.0)
    ) ** (-1.0 / power)


def equation_hyperbolic(x, power):
    x = numpy.asarray(x)
    power = numpy.asarray(power)

    return x / ((1.0 + x**power) ** (1.0 / power))


def equation_term(x, x_pivot, slope_pivot, scale):
    x = numpy.asarray(x)
    x_pivot = numpy.asarray(x_pivot)
    slope_pivot = numpy.asarray(slope_pivot)
    scale = numpy.asarray(scale)

    return (slope_pivot * (x - x_pivot)) / scale


def equation_curve(x, x_pivot, y_pivot, slope_pivot, power, scale):
    x = numpy.asarray(x)
    x_pivot = numpy.asarray(x_pivot)
    y_pivot = numpy.asarray(y_pivot)
    slope_pivot = numpy.asarray(slope_pivot)
    power = numpy.asarray(power)
    scale = numpy.asarray(scale)

    curve = numpy.where(
        scale < 0.0,
        scale
        * equation_hyperbolic(
            equation_term(x, x_pivot, slope_pivot, scale), power[..., 0]
        )
        + y_pivot,
        scale
        * equation_hyperbolic(
            equation_term(x, x_pivot, slope_pivot, scale), power[..., 1]
        )
        + y_pivot,
    )
    return curve


def equation_full_curve(x, x_pivot, y_pivot, slope_pivot, power):
    x = numpy.asarray(x)
    x_pivot = numpy.tile(numpy.asarray(x_pivot), len(x))
    y_pivot = numpy.tile(numpy.asarray(y_pivot), len(x))
    slope_pivot = numpy.tile(numpy.asarray(slope_pivot), len(x))
    power = numpy.tile(numpy.asarray(power), len(x))

    scale_x_pivot = numpy.where(x >= x_pivot, 1.0 - x_pivot, x_pivot)

    scale_y_pivot = numpy.where(x >= x_pivot, 1.0 - y_pivot, y_pivot)

    toe_scale = equation_scale(
        scale_x_pivot, scale_y_pivot, slope_pivot, power[..., 0]
    )
    shoulder_scale = equation_scale(
        scale_x_pivot, scale_y_pivot, slope_pivot, power[..., 1]
    )

    scale = numpy.where(x >= x_pivot, shoulder_scale, -toe_scale)

    return equation_curve(x, x_pivot, y_pivot, slope_pivot, power, scale)
