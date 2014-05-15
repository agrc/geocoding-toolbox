'''
Created on Apr 4, 2014

@author: kwalker
'''
import arcpy, os
from time import strftime
from GeocodeAddressTable import TableGeocoder

testing = True

if not testing:
    apiKey  = arcpy.GetParameterAsText(0)
    inputTable = arcpy.GetParameterAsText(1)
    idField = arcpy.GetParameterAsText(2)
    addressField = arcpy.GetParameterAsText(3)
    zoneField = arcpy.GetParameterAsText(4)
    locator = TableGeocoder.locatorMap[str(arcpy.GetParameterAsText(5))]
    spatialRef = TableGeocoder.spatialRefMap[str(arcpy.GetParameterAsText(6))]
    outputDir = arcpy.GetParameterAsText(7)
    outputFileName = "mapservGeocodeResults_" + strftime("%Y%m%d%H%M%S") + ".csv"
    arcpy.SetParameterAsText(6, os.path.join(outputDir, outputFileName.replace(".csv", ".dbf")))


if testing:
    apiKey = "AGRC-EB4DCEF4346265"
    inputTable = r"C:\Users\kwalker\Documents\GitHub\GeocoderTools\TableGeocoder\Data\TestData.gdb\AddressTable"
    idField = "OBJECTID"
    addressField = "ADDRESS"
    zoneField = "zone"
    locator = "roadCenterlines"
    spatialRef = 26912
    outputDir = r"C:\Users\kwalker\Documents\GitHub\GeocoderTools\TableGeocoder\Data\TestOutput"
    outputFileName =  "mapservGeocodeResults_" + strftime("%Y%m%d%H%M%S") + ".csv"


version = "2.1.0"
arcpy.AddMessage("Geocode Table Version " + version)
Tool = TableGeocoder(apiKey, inputTable, idField, addressField, zoneField, locator, spatialRef, outputDir, outputFileName)
Tool.start()
arcpy.AddMessage("Geocode completed")