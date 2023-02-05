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
import argparse
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

if __name__ == "__main__":
    #####
    # Parameters
    #####

    # Aesthetic choices for the data. Stronger shaped curves with greater slope
    # will shred the values more rapidly. If higher contrast is desired, it is
    # wiser to head into the image state with a softer shaped curve to derive
    # the signal, then apply contrast to the post formed image signal using a
    # pivoted contrast approach.
    #
    # Some folks call this "dynamic range", which is arguably nonsense. This is the
    # range of values of the origin colourimetry, before it is transformed into the
    # picture.
    normalized_log2_minimum = -10.0
    normalized_log2_maximum = +6.5

    # The input pivot point of the interstitial encoding. That is, the first stage
    # is to take the input data to a normalized log2 encoding, which creates a new
    # set of colourimetric ratios. This position is classically considered the
    # "middle" range of the soon-to-be picture / image. Here it is simply set to
    # be the "exposure" zero point of the incoming signal.
    x_pivot = numpy.abs(normalized_log2_minimum) / (
        normalized_log2_maximum - normalized_log2_minimum
    )

    # The output, or ordinate, value of the transformation. We use a simple bog
    # standard display encoding value as our final "middle" perceptual anchor.
    # Maximization of the signal to the quantised expression range should be
    # considered.
    y_pivot = 0.18 ** (1.0 / 2.2)

    # Power represents the tension in the toe and shoulder of the log encoding,
    # with the slope indicating the general slope of the linear segment.
    exponent = [1.5, 1.5]
    slope = 2.4
    argparser = argparse.ArgumentParser(
        description="Generates an OpenColorIO configuration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Rotation and scale of the individual working space primaries. Rotate is
    # in degrees, where negative is clockwise, and positive is counterclockwise.
    # Scale is in percentage relative to the primary chromaticity purity, where
    # 0.0 represents no inset scale.
    default_rotate = [4.5, -0.5, -2.0]
    default_scale = [0.15, 0.10, 0.10]
    default_achromatic_rotate = 0.0
    default_achromatic_scale = 0.0

    argparser.add_argument(
        "-et",
        "--exponent_toe",
        help="Set toe curve rate of change as an exponential power, hello Sean Cooper",
        type=float,
        default=exponent[0],
    )
    argparser.add_argument(
        "-es",
        "--exponent_shoulder",
        help="Set shoulder curve rate of change as an exponential power",
        type=float,
        default=exponent[1],
    )
    argparser.add_argument(
        "-fs",
        "--fulcrum_slope",
        help="Set central section rate of change as rise over run slope",
        type=float,
        default=slope,
    )
    argparser.add_argument(
        "-fi",
        "--fulcrum_input",
        help="Input fulcrum point relative to the normalized log2 range",
        type=float,
        default=x_pivot,
    )
    argparser.add_argument(
        "-fo",
        "--fulcrum_output",
        help="Output fulcrum point relative to the normalized log2 range",
        type=float,
        default=y_pivot,
    )
    argparser.add_argument(
        "-ll",
        "--limit_low",
        help="Lowest value of the normalized log2 range",
        type=float,
        default=normalized_log2_minimum,
    )
    argparser.add_argument(
        "-lh",
        "--limit_high",
        help="Highest value of the normalized log2 range",
        type=float,
        default=normalized_log2_maximum,
    )
    argparser.add_argument(
        "-pi",
        "--primaries_inset",
        help="Percentage of scaling inset for the primaries",
        type=float,
        nargs=3,
        default=default_scale,
    )
    argparser.add_argument(
        "-pr",
        "--primaries_rotate",
        help="Rotational adjustment in degrees for each of the RGB primaries, "
        "positive counterclockwise, negative clockwise",
        type=float,
        nargs=3,
        default=default_rotate,
    )
    argparser.add_argument(
        "-ao",
        "--achromatic_outset",
        help="Percentage of scaling outset for the achromatic coordinate",
        type=float,
        default=default_achromatic_scale,
    )
    argparser.add_argument(
        "-ar",
        "--achromatic_rotate",
        help="Rotational adjustment in degrees for the achromatic coordinate, "
        "positive counterclockwise, negative clockwise",
        type=float,
        default=default_achromatic_rotate,
    )
    argparser.add_argument(
        "-aa",
        "--achromatic_adaptation",
        help="Whether or not to perform chromatic adaptation in the restore "
        "direction of the matrix transform",
        type=bool,
        default=True,
    )

    args = argparser.parse_args()

    if args.achromatic_adaptation:
        adaptation = "CAT02"
    else:
        adaptation = None

    config = PyOpenColorIO.Config()
    description = (
        "A dangerous picture formation chain designed for Eduardo Suazo and "
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
            AgX.shape_OCIO_matrix(
                AgX.AgX_compressed_matrix(
                    primaries_rotate=args.primaries_rotate,
                    primaries_scale=args.primaries_inset,
                    achromatic_rotate=args.achromatic_rotate,
                    achromatic_outset=args.achromatic_outset,
                    adaptation=None,
                )
            )
        ),
        PyOpenColorIO.AllocationTransform(
            allocation=PyOpenColorIO.Allocation.ALLOCATION_LG2,
            vars=[
                AgX.calculate_OCIO_log2(args.limit_low),
                AgX.calculate_OCIO_log2(args.limit_high),
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
            AgX.shape_OCIO_matrix(
                AgX.AgX_compressed_matrix(
                    primaries_rotate=args.primaries_rotate,
                    primaries_scale=args.primaries_inset,
                    achromatic_rotate=args.achromatic_rotate,
                    achromatic_outset=args.achromatic_outset,
                    adaptation=adaptation,
                )
            ),
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

    x_input = numpy.linspace(0.0, 1.0, 4096)

    y_LUT = sigmoid.calculate_sigmoid(
        x_input,
        pivots=[args.fulcrum_input, args.fulcrum_output],
        slope=args.fulcrum_slope,
        powers=[args.exponent_toe, args.exponent_shoulder],
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

    for display, views in displays.items():
        # all_displays.add(display)
        for view, transform in views.items():
            all_displays.update({display: {view: transform}})
            print(
                "Adding Display: {}, View: {}, Transform: {}".format(
                    display, view, transform
                )
            )
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
