# ArcGIS Pro AGRC Web API Geocoding Toolbox

This custom toolbox created by the AGRC allows ArcGIS users to geocode a table of addresses. The geocoding tool makes use of the [AGRC Web API](https://api.mapserv.utah.gov) to perform the geocoding. A complimentary [API key](https://developer.mapserv.utah.gov) will need to be obtained to run the tool.

After the tool has completed, you will find a `.csv` and `.fgdb` with the input unique identifier field, the input address information, and the match results as fields.

The table can be joined on the unique record identifier to reconnect the results with the original data. The [make xy event layer](https://pro.arcgis.com/en/pro-app/tool-reference/data-management/make-xy-event-layer.htm) tool can be used to create points from the x, y values to spatially view the locations in a map.

ArcMap versions of this tool can be found in the [desktop-python-2](https://github.com/agrc/geocoding-toolbox/tree/desktop-python-2) branch.

## How to use

1. Download the current version of the toolbox for [ArcGIS Pro](https://github.com/agrc/geocoding-toolbox/raw/master/AGRC%20Geocode%20Tools.tbx) or [ArcGIS Desktop](https://github.com/agrc/geocoding-toolbox/raw/desktop-python-2/AGRC%20Geocode%20Tools.tbx).
1. Sign up for an [AGRC Web API account](https://developer.mapserv.utah.gov) and create a new API key using your external ip address.
1. Open `AGRC Geocode Tools.tbx` and run the tool.

## Build

There are two versions of the toolbox. `TableGeocoder/AGRC Geocode Tools.tbx` references a python script using relative paths and is for development. `AGRC Geocode Tools.tbx` (in the root of the project) is a copy of the development version with the script embedded. To cut a new release:

1. Bump the version numbers in `tool-version.json` and `TableGeocoder/GeocodeAddressTable.py`.
1. Delete `AGRC Geocode Tools.tbx` (in the root).
1. Copy `TableGeocoder/AGRC Geocode Tools.tbx` to the root folder.
1. You may need to fix the path to the script file in the newly copied toolbox tool.
1. Go to the properties of the `Geocode Table` script tool in the newly copied toolbox and select the "Import Script" checkbox.

## Testing

- Tool box without imported script that will run `GeocodeAddressTable.py` directly. This tool can be run with `GeocodeAddressTableTests.py` for a simple test.
- ArcGIS tool boxes do not accept relative paths. You will need to set the script file property of the tool box with ArcGIS Pro to the full path of `GeocodeAddressTable.py` on your machine.

## Debugging

To debug this tool outside of pro, run the tool like a normal python CLI. The following is a sample.

```sh
python GeocodeAddressTable.py AGRC-apikey "c:\path\to.csv" "id" "address" "zone" "Address points and road centerlines (default)" "NAD 1983 UTM Zone 12N" "c:\path\to\output\folder"
```

## More information

- https://gis.utah.gov/data/address-geocoders-locators/#GeocodingToolbox
- https://gis.utah.gov/developer/widgets/#arcgis-extensions
