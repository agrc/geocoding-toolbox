geocoding-addin
===============
Supports ArcGIS versions: 10.3.1, 10.4, 10.5
## Geocode Table tool
TableGeocoder\GeocodeAddressTable.py
- Implements the Geocode Table tool with the AGRC geocoding service.

### Build and Install
AGRC Geocode Tools.tbx
- AGRC Geocode Tools.tbx is the distributable ArcGIS tool box. The tool box script must be exported and then re-imported after any changes to GeocodeAddressTable.py
- AGRC Geocode Tools.tbx can be installed by adding the tool box to ArcToolbox in ArcCatalog or ArcMap.

### Testing
TableGeocoder\AGRC Geocode Tools.tbx
- Tool box without imported script that will run GeocodeAddressTable.py directly. This tool can be run with GeocodeAddressTableTests.py for a simple test.
- ArcGIS tool boxes do not accept relative paths. You will need to set the script file property of the tool box with ArcCatalog to the full path of GeocodeAddressTable.py on your machine.

###More information:
https://gis.utah.gov/data/address-geocoders-locators/#GeocodingToolbox
