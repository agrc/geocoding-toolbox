# ArcGIS Pro AGRC Web API Geocoding Add-in

This custom toolbox created by the AGRC allows ArcGIS users to geocode a table of addresses. The geocoding tool makes use of the [AGRC Web API](https://api.mapserv.utah.gov) to perform the geocoding. A complimentary [api key](https://developer.mapserv.utah.gov) will need to be obtained to run the tool. 

Aftr the tool has completed, you will find a `.csv` and `.fgdb` with the input unique identifier field, the input address information, and the match results as fields. The file geodatabase table will automatically be added to the current ArcGIS project. 

The table can be joined on the unique record identifier to reconnect the results with the original data. The [make xy event layer](https://pro.arcgis.com/en/pro-app/tool-reference/data-management/make-xy-event-layer.htm) tool can be used to create points from the x, y values to spatially view the locations in a map.

ArcMap versions of this tool can be found in the [desktop-python-2](https://github.com/agrc/geocoding-toolbox/tree/desktop-python-2) branch.

### Build and Install

- `AGRC Geocode Tools.tbx` is the distributable ArcGIS tool box. The tool box script must be exported and then re-imported after any changes to `GeocodeAddressTable.py`
- `AGRC Geocode Tools.tbx` can be installed by adding the tool box to ArcToolbox in ArcGIS Pro.

### Testing

- Tool box without imported script that will run `GeocodeAddressTable.py` directly. This tool can be run with `GeocodeAddressTableTests.py` for a simple test.
- ArcGIS tool boxes do not accept relative paths. You will need to set the script file property of the tool box with ArcGIS Pro to the full path of `GeocodeAddressTable.py` on your machine.

### More information

- https://gis.utah.gov/data/address-geocoders-locators/#GeocodingToolbox
- https://gis.utah.gov/developer/widgets/#arcmap-add-ins
