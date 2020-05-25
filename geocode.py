#!/usr/bin/env python
# * coding: utf8 *
"""
Tools for geocoding addresses using AGRC's geocoding web service.

Arguments:
    api_key
    input_table
    id_field
    address_field
    zone_field
    output_directory

Optional Arguments:
    locator
    spatial_reference
"""

import arcpy

DEFAULT_LOCATOR_NAME = 'Address points and road centerlines (default)'
DEFAULT_SPATIAL_REFERENCE = arcpy.SpatialReference(26912)


def execute(
    api_key,
    input_table,
    id_field,
    address_field,
    zone_field,
    output_directory,
    locator=DEFAULT_LOCATOR_NAME,
    spatial_reference=DEFAULT_SPATIAL_REFERENCE
):
    """the main geocoding function
    """
    pass


if __name__ == '__main__':
    #: I'm purposefully not using something like docopt here since I don't want to make
    #: Pro users install any 3rd party modules.
    from sys import argv

    #: temporary fix for https://github.com/PyCQA/pylint/issues/2820
    execute(*argv[1:])  # pylint: disable=no-value-for-parameter
