#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""AgX

The paste that holds it all together.

__author__ = Troy James Sobotka
__copyright__ = Copyright 2023
__version__ = 1.0
__maintainer__ = Troy James Sobotka
__email__ = troy.sobotka@gmail.com
__status__ = Test
"""

import numpy
import working_space
import PyOpenColorIO


def shape_OCIO_matrix(numpy_matrix):
    # Shape the RGB to XYZ array for OpenColorIO
    ocio_matrix = numpy.pad(numpy_matrix, [(0, 1), (0, 1)], mode="constant")
    ocio_matrix = ocio_matrix.flatten()
    ocio_matrix[-1] = 1.0

    return ocio_matrix


def AgX_create_colourspace(
    primaries_rotate=[1.75, -0.5, -1.0],
    primaries_scale=[0.15, 0.15, 0.10],
    tinting_rotate=0.0,
    tinting_outset=0.0,
    name="No Name Set",
):
    colourspace_destination = working_space.create_workingspace(
        primaries_rotate=primaries_rotate,
        primaries_scale=primaries_scale,
        achromatic_rotate=tinting_rotate,
        achromatic_outset=tinting_outset,
        name=name,
    )

    return colourspace_destination


def as_numeric(obj, as_type=numpy.float64):
    try:
        return as_type(obj)
    except TypeError:
        return obj


# Calculate OpenColorIO allocation for log2 from open domain tristimulus value.
def calculate_OCIO_log2(in_ev, od_middle_grey=0.18):
    return numpy.log2(numpy.power(2.0, in_ev) * od_middle_grey)


# Convert relative exposure values open domain tristimulus values.
def calculate_ev_to_od(in_ev, od_middle_grey=0.18):
    in_ev = numpy.asarray(in_ev)

    return as_numeric(numpy.power(2.0, in_ev) * od_middle_grey)


# Convert open domain tristimulus values to relative expsoure values.
def calculate_od_to_ev(in_od, od_middle_grey=0.18):
    in_od = numpy.asarray(in_od)

    return as_numeric(numpy.log2(in_od) - numpy.log2(od_middle_grey))


def adjust_exposure(RGB_input, exposure_adjustment):
    return numpy.power(2.0, exposure_adjustment) * RGB_input


def open_domain_to_normalized_log2(
    in_od, in_middle_grey=0.18, minimum_ev=-7.0, maximum_ev=+7.0
):
    total_exposure = maximum_ev - minimum_ev

    in_od = numpy.asarray(in_od)
    in_od[in_od <= 0.0] = numpy.finfo(float).eps

    output_log = numpy.clip(
        numpy.log2(in_od / in_middle_grey), minimum_ev, maximum_ev
    )

    return as_numeric((output_log - minimum_ev) / total_exposure)


def normalized_log2_to_open_domain(
    in_norm_log2, od_middle_grey=0.18, minimum_ev=-7.0, maximum_ev=+7.0
):
    in_norm_log2 = numpy.asarray(in_norm_log2)

    in_norm_log2 = (
        numpy.clip(in_norm_log2, 0.0, 1.0) * (maximum_ev - minimum_ev)
        + minimum_ev
    )

    return as_numeric(numpy.power(2.0, in_norm_log2) * od_middle_grey)


# The following is a completely tunable sigmoid function compliments
# of the incredible hard work of Jed Smith. He's an incredible peep,
# but don't let anyone know that I said that.
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


def add_view(in_dict, display, view_name, view_transform):
    if display not in in_dict:
        in_dict[display] = {}
    in_dict[display][view_name] = view_transform

    return in_dict


def add_colourspace(
    config,
    family,
    name,
    description,
    transforms=None,
    aliases=[],
    direction=PyOpenColorIO.ColorSpaceDirection.COLORSPACE_DIR_FROM_REFERENCE,
    referencespace=PyOpenColorIO.ReferenceSpaceType.REFERENCE_SPACE_SCENE,
    isdata=False,
    debug=False,
):
    colourspace_family = family
    colourspace_name = name
    colourspace_description = description

    colourspace = PyOpenColorIO.ColorSpace(
        referenceSpace=referencespace,
        family=colourspace_family,
        name=colourspace_name,
        aliases=aliases,
        isData=isdata,
    )
    colourspace.setDescription(colourspace_description)

    if transforms is not None:
        if len(transforms) > 1:
            transforms = PyOpenColorIO.GroupTransform(transforms)
        else:
            transforms = transforms[0]

        colourspace.setTransform(transforms, direction)

    if debug is True:
        # DEBUG
        shader_desc = PyOpenColorIO.GpuShaderDesc.CreateShaderDesc(
            language=PyOpenColorIO.GPU_LANGUAGE_GLSL_4_0
        )
        processor = config.getProcessor(transforms).getDefaultGPUProcessor()
        processor.extractGpuShaderInfo(shader_desc)
        print("*****[{}]:\n{}".format(name, shader_desc.getShaderText()))

    config.addColorSpace(colourspace)

    return config, colourspace


def add_named_transform(
    config, family, name, description, transforms, aliases=None
):
    if isinstance(transforms, list):
        transform = PyOpenColorIO.GroupTransform(transforms)

    named_transform = PyOpenColorIO.NamedTransform(
        name=name, aliases=aliases, family=family, forwardTransform=transform
    )

    named_transform.setDescription(description)

    config.addNamedTransform(named_transform)

    return config, named_transform


def add_look(
    config,
    name,
    transforms,
    description,
    processSpace="AgX Base",
):
    if len(transforms) > 1:
        transforms = PyOpenColorIO.GroupTransform(transforms)
    else:
        transforms = transforms[0]

    look = PyOpenColorIO.Look(
        name=name,
        processSpace=processSpace,
        transform=transforms,
        description=description,
    )

    config.addLook(look)

    return config, look
