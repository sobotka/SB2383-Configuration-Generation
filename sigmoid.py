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
# def equation_scale(x_pivot, y_pivot, slope_pivot, power):
#     x_pivot = numpy.asarray(x_pivot)
#     y_pivot = numpy.asarray(y_pivot)
#     slope_pivot = numpy.asarray(slope_pivot)
#     power = numpy.asarray(power)

#     return (
#         ((slope_pivot * x_pivot) ** -power)
#         * (((slope_pivot * (x_pivot / y_pivot)) ** power) - 1.0)
#     ) ** (-1.0 / power)


# def equation_hyperbolic(x, power):
#     x = numpy.asarray(x)
#     power = numpy.asarray(power)

#     return x / ((1.0 + x**power) ** (1.0 / power))


# def equation_term(x, x_pivot, slope_pivot, scale):
#     x = numpy.asarray(x)
#     x_pivot = numpy.asarray(x_pivot)
#     slope_pivot = numpy.asarray(slope_pivot)
#     scale = numpy.asarray(scale)

#     return (slope_pivot * (x - x_pivot)) / scale


# def equation_curve(x, x_pivot, y_pivot, slope_pivot, power, scale):
#     x = numpy.asarray(x)
#     x_pivot = numpy.asarray(x_pivot)
#     y_pivot = numpy.asarray(y_pivot)
#     slope_pivot = numpy.asarray(slope_pivot)
#     power = numpy.asarray(power)
#     scale = numpy.asarray(scale)

#     curve = numpy.where(
#         scale < 0.0,
#         scale
#         * equation_hyperbolic(
#             equation_term(x, x_pivot, slope_pivot, scale), power[..., 0]
#         )
#         + y_pivot,
#         scale
#         * equation_hyperbolic(
#             equation_term(x, x_pivot, slope_pivot, scale), power[..., 1]
#         )
#         + y_pivot,
#     )
#     return curve


# def equation_full_curve(x, x_pivot, y_pivot, slope_pivot, power):
#     x = numpy.asarray(x)
#     x_pivot = numpy.tile(numpy.asarray(x_pivot), len(x))
#     y_pivot = numpy.tile(numpy.asarray(y_pivot), len(x))
#     slope_pivot = numpy.tile(numpy.asarray(slope_pivot), len(x))
#     power = numpy.tile(numpy.asarray(power), len(x))

#     scale_x_pivot = numpy.where(x >= x_pivot, 1.0 - x_pivot, x_pivot)

#     scale_y_pivot = numpy.where(x >= x_pivot, 1.0 - y_pivot, y_pivot)

#     toe_scale = equation_scale(
#         scale_x_pivot, scale_y_pivot, slope_pivot, power[..., 0]
#     )
#     shoulder_scale = equation_scale(
#         scale_x_pivot, scale_y_pivot, slope_pivot, power[..., 1]
#     )

#     scale = numpy.where(x >= x_pivot, shoulder_scale, -toe_scale)

#     return equation_curve(x, x_pivot, y_pivot, slope_pivot, power, scale)


def linear_breakpoint(numerator, slope, coordinate):
    denominator = numpy.ma.power(
        numpy.ma.power(slope, 2.0).filled(fill_value=0.0) + 1.0, 1.0 / 2.0
    ).filled(fill_value=0.0)

    return numpy.ma.divide(numerator, denominator) + coordinate


def line(x_in, slope, intercept):
    return numpy.ma.add(numpy.ma.multiply(slope, x_in), intercept)


def scale(limit_x, limit_y, transition_x, transition_y, power, slope):
    term_a = numpy.ma.power(
        numpy.ma.multiply(slope, numpy.ma.subtract(limit_x, transition_x)),
        -power,
    ).filled(fill_value=0.0)

    term_b = numpy.ma.subtract(
        numpy.ma.power(
            numpy.ma.divide(
                numpy.ma.multiply(
                    slope, numpy.ma.subtract(limit_x, transition_x)
                ),
                numpy.ma.subtract(limit_y, transition_y),
            ),
            power,
        ).filled(fill_value=0.0),
        1.0,
    )

    return numpy.ma.power(
        numpy.ma.multiply(term_a, term_b), -numpy.ma.divide(1.0, power)
    ).filled(fill_value=0.0)


def exponential(x_in, power):
    return numpy.ma.divide(
        x_in,
        numpy.ma.power(
            numpy.ma.add(1.0, numpy.ma.power(x_in, power)),
            numpy.ma.divide(1.0, power),
        ),
    )


def exponential_curve(x_in, scale, slope, power, transition_x, transition_y):
    return numpy.ma.add(
        numpy.ma.multiply(
            scale,
            exponential(
                numpy.ma.divide(
                    numpy.ma.multiply(
                        slope, numpy.ma.subtract(x_in, transition_x)
                    ),
                    scale,
                ),
                power,
            ),
        ),
        transition_y,
    )


def calculate_sigmoid(
    # Input x
    x_in,
    # Pivot coordinates x and y for the fulcrum.
    pivots=[0.5, 0.5],
    # Slope of linear portion.
    slope=2.0,
    # Length of transition toward the toe and shoulder.
    lengths=[0.0, 0.0],
    # Exponential power of the toe and shoulder regions.
    powers=[1.0, 1.0],
    # Intersection limit coordinates x and y for the toe and shoulder.
    limits=[[0.0, 0.0], [1.0, 1.0]],
):
    pivots = numpy.asarray(pivots)
    lengths = numpy.asarray(lengths)
    powers = numpy.asarray(powers)
    limits = numpy.asarray(limits)

    # t_tx
    transition_toe_x = linear_breakpoint(-lengths[0], slope, pivots[0])
    # print("transition_toe_x: {}".format(transition_toe_x))

    # t_ty
    transition_toe_y = linear_breakpoint(
        numpy.ma.multiply(slope, -lengths[0]), slope, pivots[1]
    )
    # print("transition_toe_y: {}".format(transition_toe_y))

    # s_tx
    transition_shoulder_x = linear_breakpoint(lengths[1], slope, pivots[0])
    # print("transition_shoulder_x: {}".format(transition_shoulder_x))

    # s_ty
    transition_shoulder_y = linear_breakpoint(
        numpy.ma.multiply(slope, lengths[1]), slope, pivots[1]
    )
    # print("transition_shoulder_y: {}".format(transition_shoulder_y))

    # t_itx
    inverse_transition_toe_x = numpy.ma.subtract(1.0, transition_toe_x)
    # print("inverse_transition_toe_x: {}".format(inverse_transition_toe_x))

    # t_ity
    inverse_transition_toe_y = numpy.ma.subtract(1.0, transition_toe_y)
    # print("inverse_transition_toe_y: {}".format(inverse_transition_toe_y))

    # t_ilx
    inverse_limit_toe_x = numpy.ma.subtract(1.0, limits[0, 0])
    # print("inverse_limit_toe_x: {}".format(inverse_limit_toe_x))

    # t_ily
    inverse_limit_toe_y = numpy.ma.subtract(1.0, limits[0, 1])
    # print("inverse_limit_toe_y: {}".format(inverse_limit_toe_y))

    scale_toe = -scale(
        limit_x=inverse_limit_toe_x,
        limit_y=inverse_limit_toe_y,
        transition_x=inverse_transition_toe_x,
        transition_y=inverse_transition_toe_y,
        power=powers[0],
        slope=slope,
    )
    # print("scale_toe: {}".format(scale_toe))

    scale_shoulder = scale(
        limit_x=limits[1, 0],
        limit_y=limits[1, 1],
        transition_x=transition_shoulder_x,
        transition_y=transition_shoulder_y,
        power=powers[1],
        slope=slope,
    )
    # print("scale_shoulder: {}".format(scale_shoulder))

    # b
    intercept = numpy.ma.subtract(
        transition_toe_y, numpy.ma.multiply(slope, transition_toe_x)
    )

    return numpy.where(
        x_in < transition_toe_x,
        exponential_curve(
            x_in,
            scale_toe,
            slope,
            powers[0],
            transition_toe_x,
            transition_toe_y,
        ),
        numpy.where(
            x_in <= transition_shoulder_x,
            line(x_in, slope, intercept),
            exponential_curve(
                x_in,
                scale_shoulder,
                slope,
                powers[1],
                transition_shoulder_x,
                transition_shoulder_y,
            ),
        ),
    )
