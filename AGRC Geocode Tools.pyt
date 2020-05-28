#!/usr/bin/env python
# * coding: utf8 *
"""
A python toolbox
"""
# pylint: disable=invalid-name

import arcpy
import geocode

#: to force refresh of the module in ArcGIS Pro - for development only
# import importlib  # isort:skip
# importlib.reload(geocode)

LOCATORS = {
    'Address points and road centerlines': 'all',
    'Road centerlines': 'roadCenterlines',
    'Address points': 'addressPoints'
}


class Toolbox():
    """Esri Python Toolbox
    """

    def __init__(self):
        self.label = 'AGRC Geocoding Tools'
        self.alias = ''

        self.tools = [GeocodeTable]


class GeocodeTable():
    """Geocode Table Tool
    """

    def __init__(self):
        self.label = 'Geocode Table'
        self.description = 'Geocode street addresses using AGRC\'s geocoding web service.'

    def getParameterInfo(self):
        """Define parameter definitions
        """

        api_key_parameter = arcpy.Parameter(
            name='api_key', displayName='API Key', datatype='GPString', parameterType='Required', direction='Input'
        )
        table_parameter = arcpy.Parameter(
            name='input_table',
            displayName='Input Table',
            datatype='GPTableView',
            parameterType='Required',
            direction='Input'
        )
        id_field_parameter = arcpy.Parameter(
            name='id_field', displayName='ID Field', datatype='Field', parameterType='Required', direction='Input'
        )
        id_field_parameter.parameterDependencies = [table_parameter.name]

        address_field_parameter = arcpy.Parameter(
            name='address_field',
            displayName='Address Field',
            datatype='Field',
            parameterType='Required',
            direction='Input'
        )
        address_field_parameter.parameterDependencies = [table_parameter.name]

        zone_field_parameter = arcpy.Parameter(
            name='zone_field', displayName='Zone Field', datatype='Field', parameterType='Required', direction='Input'
        )
        zone_field_parameter.parameterDependencies = [table_parameter.name]

        output_directory_parameter = arcpy.Parameter(
            name='output_directory',
            displayName='Output Directory',
            datatype='DEWorkspace',
            parameterType='Required',
            direction='Input'
        )

        spatial_reference_parameter = arcpy.Parameter(
            name='spatial_reference',
            displayName='Spatial Reference',
            datatype='GPSpatialReference',
            parameterType='Required',
            direction='Input'
        )
        spatial_reference_parameter.value = arcpy.SpatialReference(geocode.DEFAULT_SPATIAL_REFERENCE)

        locator_parameter = arcpy.Parameter(
            name='locator',
            displayName='Locator',
            datatype='GPString',
            parameterType='Required',
            direction='Input',
        )
        locator_parameter.filter.type = 'ValueList'
        locator_parameter.filter.list = list(LOCATORS.keys())
        locator_parameter.value = list(LOCATORS.keys())[0]

        output_csv_parameter = arcpy.Parameter(
            name='output_csv',
            displayName='Output CSV',
            datatype='DETable',
            parameterType='Derived',
            direction='Output'
        )

        return [
            api_key_parameter, table_parameter, id_field_parameter, address_field_parameter, zone_field_parameter,
            output_directory_parameter, spatial_reference_parameter, locator_parameter, output_csv_parameter
        ]

    def execute(self, parameters, messages):
        """pass parameters to main geocoding module and set output csv parameter
        """
        api_key_parameter, table_parameter, id_field_parameter, address_field_parameter, zone_field_parameter, \
            output_directory_parameter, spatial_reference_parameter, locator_parameter, \
                output_csv_parameter = parameters

        wkid = str(spatial_reference_parameter.value.factoryCode)
        locators = LOCATORS[locator_parameter.valueAsText]

        fields = [id_field_parameter.valueAsText, address_field_parameter.valueAsText, zone_field_parameter.valueAsText]
        rows = arcpy.da.SearchCursor(table_parameter.valueAsText, fields)
        output_table = geocode.execute(
            api_key_parameter.valueAsText,
            rows,
            output_directory_parameter.valueAsText,
            wkid,
            locators,
            add_message=messages.addMessage
        )

        output_csv_parameter.value = str(output_table)
