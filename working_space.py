#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""working_space

Generate the working space according to general inset outset principles.

__author__ = Troy James Sobotka
__copyright__ = Copyright 2023
__version__ = 1.0
__maintainer__ = Troy James Sobotka
__email__ = troy.sobotka@gmail.com
__status__ = Test
"""

import colour
import numpy
import shapely
import shapely.affinity


def create_workingspace(
    primaries_rotate=[1.75, -0.5, -1.0],
    primaries_scale=[0.15, 0.15, 0.10],
    colourspace_in=colour.RGB_COLOURSPACES["ITU-R BT.709"],
):
    #####
    # Construct the Base Image Formation Colourspace
    #####

    point_red = shapely.Point(colourspace_in.primaries[0])
    point_green = shapely.Point(colourspace_in.primaries[1])
    point_blue = shapely.Point(colourspace_in.primaries[2])
    point_achromatic = shapely.Point(colourspace_in.whitepoint)

    # Scale the primaries outward by some safe and arbitrary amount.
    scaled_red = shapely.affinity.scale(
        point_red, xfact=2.0, yfact=2.0, origin=point_achromatic
    )
    scaled_green = shapely.affinity.scale(
        point_green, xfact=2.0, yfact=2.0, origin=point_achromatic
    )

    scaled_blue = shapely.affinity.scale(
        point_blue, xfact=2.0, yfact=2.0, origin=point_achromatic
    )

    # Rotate the primaries to gently nudge the distortions toward the Tritan
    # confusion axis through achromatic. Positive values are counter clockwise.
    rotate_red = primaries_rotate[0]
    rotate_green = primaries_rotate[1]
    rotate_blue = primaries_rotate[2]

    rotated_out_red = shapely.affinity.rotate(
        scaled_red, rotate_red, origin=point_achromatic
    )
    rotated_out_green = shapely.affinity.rotate(
        scaled_green, rotate_green, origin=point_achromatic
    )
    rotated_out_blue = shapely.affinity.rotate(
        scaled_blue, rotate_blue, origin=point_achromatic
    )

    # Generate bisecting lines.
    rotated_out_lines = shapely.geometry.MultiLineString(
        [
            [rotated_out_red, point_achromatic],
            [rotated_out_green, point_achromatic],
            [rotated_out_blue, point_achromatic],
        ]
    )

    working_polygon = shapely.geometry.Polygon(colourspace_in.primaries)

    # Calculate the intersections with the working space chosen.
    intersections = working_polygon.intersection(rotated_out_lines)

    hull_rotated_points = []
    for intersection in intersections.geoms:
        hull_rotated_points.append(
            [intersection.coords.xy[0][0], intersection.coords.xy[1][0]]
        )

    scale_red_in = primaries_scale[0]
    scale_green_in = primaries_scale[1]
    scale_blue_in = primaries_scale[2]

    hull_red = shapely.geometry.Point(hull_rotated_points[0])
    hull_green = shapely.geometry.Point(hull_rotated_points[1])
    hull_blue = shapely.geometry.Point(hull_rotated_points[2])

    # Inset according to the desired inset scales. Insetting controls the rate
    # of attenuation.
    rotated_inset_red = shapely.affinity.scale(
        hull_red,
        xfact=(1.0 - scale_red_in),
        yfact=(1.0 - scale_red_in),
        origin=point_achromatic,
    )

    rotated_inset_green = shapely.affinity.scale(
        hull_green,
        xfact=(1.0 - scale_green_in),
        yfact=(1.0 - scale_green_in),
        origin=point_achromatic,
    )

    rotated_inset_blue = shapely.affinity.scale(
        hull_blue,
        xfact=(1.0 - scale_blue_in),
        yfact=(1.0 - scale_blue_in),
        origin=point_achromatic,
    )

    primaries_inset = numpy.asarray(
        [
            rotated_inset_red.coords,
            rotated_inset_green.coords[:],
            rotated_inset_blue.coords[:],
        ]
    )

    colourspace_sb2383 = colour.RGB_Colourspace(
        name="SouzaBrejon2383 Inset",
        primaries=primaries_inset,
        whitepoint=colourspace_in.whitepoint,
        whitepoint_name=colourspace_in.whitepoint_name,
        cctf_encoding=colourspace_in.cctf_encoding,
        cctf_decoding=colourspace_in.cctf_decoding,
        use_derived_matrix_RGB_to_XYZ=True,
        use_derived_matrix_XYZ_to_RGB=True,
    )

    return colourspace_sb2383
