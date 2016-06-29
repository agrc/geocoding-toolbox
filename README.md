geocoding-addin
===============

## Geocode Table tool
TableGeocoder\GeocodeAddressTable.py
- Implements the Geocode Table tool with the AGRC Multiple Address geocoding service.

### Build and Install
AGRC Geocode Tools.tbx
- AGRC Geocode Tools.tbx is the distributable ArcGIS tool box. The tool box script must be exported and then re-imported after any changes to GeocodeAddressTable.py
- AGRC Geocode Tools.tbx can be installed by adding the tool box to ArcToolbox in ArcCatalog or ArcMap.

### Testing
TableGeocoder\AGRC Geocode Tools.tbx
- Tool box without imported script that will run GeocodeAddressTable.py directly. This tool can be run with TableGeocoder\Data\TestData.gdb\AddressTable for a simple manual test.
- ArcGIS tool boxes do not accept relative paths. You will need to set the script file property of the tool box with ArcCatalog to the full path of GeocodeAddressTable.py on your machine.

###More information:
http://gis.utah.gov/new-utah-geocoding-toolbox-for-arcgis-desktop-2/
