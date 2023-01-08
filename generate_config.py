#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""generate_config

Generate the working configuration according to general inset outset principles.

__author__ = Troy James Sobotka
__copyright__ = Copyright 2023
__version__ = 1.0
__maintainer__ = Troy James Sobotka
__email__ = troy.sobotka@gmail.com
__status__ = Test
"""

import PyOpenColorIO
import numpy
import colour
import pathlib
import AgX
import sigmoid

####
# Global Configuration Variables
####
output_config_directory = "./config/"
output_config_name = "config.ocio"
output_LUTs_directory = "./LUTs/"
LUT_search_paths = ["LUTs"]

supported_displays = {
    "Display P3": {
        "Display Native": "Display P3 Display",
        "AgX": "AgX Display P3 Display",
    },
    "sRGB": {"Display Native": "sRGB Display", "AgX": "AgX sRGB Display"},
    "BT.1886": {
        "Display Native": "Display P3 Display",
        "AgX": "AgX BT.1886 Display",
    },
}

AgX_min_log2 = -10.0
AgX_max_log2 = +6.5
AgX_x_pivot = numpy.abs(AgX_min_log2 / (AgX_max_log2 - AgX_min_log2))
AgX_y_pivot = 0.50

if __name__ == "__main__":
    config = PyOpenColorIO.Config()
    description = (
        "A dangerous picutre formation chain designed for Eduardo Suazo and "
        "Chris Brejon."
    )
    config.setDescription(description)
    config.setMinorVersion(0)

    config.setSearchPath(":".join(LUT_search_paths))

    # Establish a displays dictionary to track the displays. Append
    # the respective display at each of the display colourspace definitions
    # for clarity.
    displays = {}

    # Establish a colourspaces dictionary for fetching colourspace objects.
    colourspaces = {}

    ####
    # Colourspaces
    ####

    # Define a generic tristimulus linear working space, with assumed
    # BT.709 primaries and a D65 achromatic point.
    config, colourspace = AgX.add_colourspace(
        config=config,
        family="Colourspaces",
        name="Linear BT.709",
        description="Open Domain Linear BT.709 Tristimulus",
        aliases=["Linear", "Linear Tristimulus"],
    )

    # AgX
    transform_list = [
        PyOpenColorIO.RangeTransform(minInValue=0.0, minOutValue=0.0),
        PyOpenColorIO.MatrixTransform(
            AgX.shape_OCIO_matrix(AgX.AgX_compressed_matrix())
        ),
        PyOpenColorIO.AllocationTransform(
            allocation=PyOpenColorIO.Allocation.ALLOCATION_LG2,
            vars=[
                AgX.calculate_OCIO_log2(AgX_min_log2),
                AgX.calculate_OCIO_log2(AgX_max_log2),
            ],
        ),
    ]

    config, colourspace = AgX.add_colourspace(
        config=config,
        family="Log Encodings",
        name="AgX Log (SB2383)",
        description="AgX Log, (SB2383)",
        aliases=["Log", "AgX Log", "SB2383", "AgX SB2383 Log"],
        transforms=transform_list,
    )

    ####
    # Utilities
    ####

    # Define a generic 2.2 Electro Optical Transfer Function
    transform_list = [
        PyOpenColorIO.ExponentTransform(
            value=[2.2, 2.2, 2.2, 1.0],
            direction=PyOpenColorIO.TransformDirection.TRANSFORM_DIR_INVERSE,
        )
    ]

    config, colourspace = AgX.add_colourspace(
        config=config,
        family="Utilities/Curves",
        name="2.2 EOTF Encoding",
        description="2.2 Exponent EOTF Encoding",
        aliases=["2.2 EOTF Encoding", "sRGB EOTF Encoding"],
        transforms=transform_list,
    )

    # Define a generic 2.4 Electro Optical Transfer Function
    transform_list = [
        PyOpenColorIO.ExponentTransform(
            value=[2.4, 2.4, 2.4, 1.0],
            direction=PyOpenColorIO.TransformDirection.TRANSFORM_DIR_INVERSE,
        )
    ]

    config, colourspace = AgX.add_colourspace(
        config=config,
        family="Utilities/Curves",
        name="2.4 EOTF Encoding",
        description="2.4 Exponent EOTF Encoding",
        aliases=["2.4 EOTF Encoding", "BT.1886 EOTF Encoding"],
        transforms=transform_list,
    )

    ####
    # Displays
    ####

    # Define the specification sRGB Display colourspace
    transform_list = [
        PyOpenColorIO.ColorSpaceTransform(
            src="Linear BT.709", dst="2.2 EOTF Encoding"
        )
    ]

    config, colourspace = AgX.add_colourspace(
        config=config,
        family="Displays/SDR",
        name="sRGB",
        description="sRGB IEC 61966-2-1 2.2 Exponent Reference EOTF Display",
        transforms=transform_list,
        referencespace=PyOpenColorIO.ReferenceSpaceType.REFERENCE_SPACE_SCENE,
    )

    # TODO: Move this to a different section.
    AgX.add_view(displays, "sRGB", "Display Native", "sRGB")

    # Add Display P3.
    Display_P3_Colourspace = colour.RGB_COLOURSPACES["Display P3"]
    sRGB_Colourspace = colour.RGB_COLOURSPACES["sRGB"]
    D_P3_RGB_to_sRGB_matrix = colour.matrix_RGB_to_RGB(
        sRGB_Colourspace, Display_P3_Colourspace
    )

    transform_list = [
        PyOpenColorIO.MatrixTransform(
            AgX.shape_OCIO_matrix(D_P3_RGB_to_sRGB_matrix)
        ),
        PyOpenColorIO.ColorSpaceTransform(
            src="Linear BT.709", dst="2.2 EOTF Encoding"
        ),
    ]

    config, colourspace = AgX.add_colourspace(
        config=config,
        family="Displays/SDR",
        name="Display P3",
        description="Display P3 2.2 Exponent EOTF Display",
        transforms=transform_list,
        referencespace=PyOpenColorIO.ReferenceSpaceType.REFERENCE_SPACE_SCENE,
    )

    # TODO: Move this to a different section.
    AgX.add_view(displays, "Display P3", "Display Native", "Display P3")

    # Add BT.1886.
    transform_list = [
        PyOpenColorIO.ColorSpaceTransform(
            src="Linear BT.709", dst="2.4 EOTF Encoding"
        )
    ]

    config, colourspace = AgX.add_colourspace(
        config=config,
        family="Displays/SDR",
        name="BT.1886",
        description="BT.1886 2.4 Exponent EOTF Display",
        transforms=transform_list,
        referencespace=PyOpenColorIO.ReferenceSpaceType.REFERENCE_SPACE_SCENE,
    )

    # TODO: Move this to a different section.
    AgX.add_view(displays, "BT.1886", "Display Native", "BT.1886")

    ####
    # Views
    ####

    # Add AgX SB2383 aesthetic image base.
    transform_list = [
        PyOpenColorIO.ColorSpaceTransform(
            src="Linear BT.709", dst="AgX Log (SB2383)"
        ),
        PyOpenColorIO.FileTransform(src="AgX_Default_Contrast.spi1d"),
        PyOpenColorIO.ExponentTransform(
            value=[2.2, 2.2, 2.2, 1.0],
            direction=PyOpenColorIO.TransformDirection.TRANSFORM_DIR_FORWARD,
        ),
        PyOpenColorIO.MatrixTransform(
            AgX.shape_OCIO_matrix(AgX.AgX_compressed_matrix()),
            direction=PyOpenColorIO.TransformDirection.TRANSFORM_DIR_INVERSE,
        ),
        PyOpenColorIO.ExponentTransform(
            value=[2.2, 2.2, 2.2, 1.0],
            direction=PyOpenColorIO.TransformDirection.TRANSFORM_DIR_INVERSE,
        ),
    ]

    config, colourspace = AgX.add_colourspace(
        config=config,
        family="Image Formation",
        name="AgX Base",
        description="AgX Base Image Encoding",
        transforms=transform_list,
        referencespace=PyOpenColorIO.ReferenceSpaceType.REFERENCE_SPACE_SCENE,
    )

    # TODO: Move this to a different section.
    AgX.add_view(displays, "sRGB", "AgX", "AgX Base")

    # Add BT.1886 AgX SB2383 aesthetic image base.
    transform_list = [
        PyOpenColorIO.ColorSpaceTransform(src="Linear BT.709", dst="AgX Base"),
        PyOpenColorIO.ColorSpaceTransform(
            src="2.2 EOTF Encoding", dst="2.4 EOTF Encoding"
        ),
    ]

    config, colourspace = AgX.add_colourspace(
        config=config,
        family="Views/AgX BT.1886",
        name="AgX Base BT.1886",
        description="AgX Base Image Encoding for BT.1886 Displays",
        transforms=transform_list,
        referencespace=PyOpenColorIO.ReferenceSpaceType.REFERENCE_SPACE_SCENE,
    )

    # TODO: Move this to a different section.
    AgX.add_view(displays, "BT.1886", "AgX", "AgX Base BT.1886")

    # Add Display P3 AgX SB2383 aesthetic image base.
    transform_list = [
        PyOpenColorIO.ColorSpaceTransform(src="Linear BT.709", dst="AgX Base"),
        PyOpenColorIO.ColorSpaceTransform(
            src="2.2 EOTF Encoding", dst="Display P3"
        ),
    ]

    config, colourspace = AgX.add_colourspace(
        config=config,
        family="Views/AgX Display P3",
        name="AgX Base Display P3",
        description="AgX Base Image Encoding for Display P3 Displays",
        transforms=transform_list,
        referencespace=PyOpenColorIO.ReferenceSpaceType.REFERENCE_SPACE_SCENE,
    )

    # TODO: Move this to a different section.
    AgX.add_view(displays, "Display P3", "AgX", "AgX Base Display P3")

    ####
    # Appearances / Looks
    ####

    ####
    # Data
    ####

    config, colourspace = AgX.add_colourspace(
        config=config,
        family="Data/Generic Data",
        name="Generic Data",
        aliases=["Non-Color", "Raw"],
        description="Generic data encoding",
        isdata=True,
    )

    ####
    # Creative Looks LUTs
    ###

    #####
    # Curve Setup
    #####

    # Aesthetic choices for the curve. Stronger shaped curves with greater slope
    # will shred the values more rapidly. If higher contrast is desired, it is
    # wiser to head into the image state with a softer shaped curve to derive
    # the signal, then apply contrast to the post formed image signal using a
    # pivoted contrast approach.
    #
    # Power represents the tension in the toe and shoulder of the log encoding,
    # with the slope indicating the general slope of the linear segment.
    power = [1.5, 1.5]
    slope = 2.4

    x_input = numpy.linspace(0.0, 1.0, 4096)
    normalized_log2_minimum = AgX_min_log2
    normalized_log2_maximum = AgX_max_log2
    x_pivot = numpy.abs(normalized_log2_minimum) / (
        normalized_log2_maximum - normalized_log2_minimum
    )
    y_pivot = 0.18 ** (1.0 / 2.2)

    y_LUT = sigmoid.equation_full_curve(
        x_input, x_pivot, y_pivot, slope, power
    )

    aesthetic_LUT_name = "AgX Default Contrast"
    aesthetic_LUT_safe = aesthetic_LUT_name.replace(" ", "_")
    aesthetic_LUT = colour.LUT1D(table=y_LUT, name="AgX Default Contrast")

    try:
        output_directory = pathlib.Path(output_config_directory)
        LUTs_directory = output_directory / output_LUTs_directory
        LUT_filename = pathlib.Path(
            LUTs_directory / "{}.spi1d".format(aesthetic_LUT_safe)
        )
        LUTs_directory.mkdir(parents=True, exist_ok=True)
        colour.io.luts.write_LUT(
            aesthetic_LUT, LUT_filename, method="Sony SPI1D"
        )

    except Exception as ex:
        raise ex

    ####
    # Config Generation
    ####

    roles = {
        # "cie_xyz_d65_interchange":,
        "color_picking": "sRGB",
        "color_timing": "sRGB",
        "compositing_log": "sRGB",
        "data": "Generic Data",
        "default": "sRGB",
        "default_byte": "sRGB",
        "default_float": "Linear BT.709",
        "default_sequencer": "sRGB",
        "matte_paint": "sRGB",
        "reference": "Linear BT.709",
        "scene_linear": "Linear BT.709",
        "texture_paint": "sRGB",
    }

    for role, transform in roles.items():
        config.setRole(role, transform)

    all_displays = {}
    all_views = {}

    print(displays.items())
    for display, views in displays.items():
        # all_displays.add(display)
        for view, transform in views.items():
            all_displays.update({display: {view: transform}})
            print("Adding {} {} {}".format(display, view, transform))
            config.addDisplayView(
                display=display, view=view, colorSpaceName=transform
            )

    try:
        config.validate()

        output_directory = pathlib.Path(output_config_directory)
        output_directory.mkdir(parents=True, exist_ok=True)
        output_file = output_directory / output_config_name

        write_file = open(output_file, "w")
        write_file.write(config.serialize())
        write_file.close()
        print('Wrote config "{}"'.format(output_config_name))
    except Exception as ex:
        raise ex
