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

## Releasing

There is a `cut_release.py` CLI to bump and package releases.

1. Install the CLI dependencies
   `pip install -r requirements.dev.txt`
1. Cut a release with the CLI
   `python cut_release.py minor`
   - To see the full options of the CLI use `python cut_release.py --help
1. Push the release commit to GitHub
