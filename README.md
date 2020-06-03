# AGRC Geocoding Toolbox

[![Build Status](https://travis-ci.com/agrc/geocoding-toolbox.svg?branch=master)](https://travis-ci.com/agrc/geocoding-toolbox) [![Coverage Status](https://coveralls.io/repos/github/agrc/geocoding-toolbox/badge.svg?branch=master)](https://coveralls.io/github/agrc/geocoding-toolbox?branch=master) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This custom toolbox created by the AGRC allows ArcGIS users to geocode a table of addresses. The geocoding tool makes use of the [AGRC Web API](https://api.mapserv.utah.gov/#geocoding) to perform the geocoding. A complimentary [API key](https://developer.mapserv.utah.gov/secure/Home) will need to be obtained to run the tool.

After the tool has completed, you will find a `.csv` with the input unique identifier field, the input address information, and the match results as fields.

The table can be joined on the unique record identifier to reconnect the results with the original data. The [make xy event layer](https://pro.arcgis.com/en/pro-app/tool-reference/data-management/make-xy-event-layer.htm) tool can be used to create points from the x, y values to spatially view the locations in a map.

## ArcGIS Support

This tool uses the python requests package that was bundled into ArcGIS Pro at version 1.3. Therefore, this tool is supported by ArcGIS Pro 1.3 or greater.

You can install requests into your ArcGIS Pro conda environment if you cannot upgrade to version 1.3 or greater.

This toolbox can be imported via `arcpy` just like any other custom toolbox:

```py
arcpy.ImportToolbox(r'<path to folder>\AGRC Geocode Tools.pyt')
arcpy.agrcgeocoding.GeocodeTable('AGRC-99999999999999', r'C:\temp\tests\normal.csv', 'id', 'street', 'zone', r'C:\temp')
```

## Installation

1. Sign up for an [AGRC Web API account](https://developer.mapserv.utah.gov) and create a new "Server" API key using your external ip address.
1. Download the [ArcGIS Pro Geocoding Tool for python 3](https://github.com/agrc/geocoding-toolbox/raw/master/tool/AGRC%20Geocode%20Tools.zip) or the less recommended [ArcGIS Desktop Geocoding Tool for python 2](https://github.com/agrc/geocoding-toolbox/raw/py-2/tool/AGRC%20Geocode%20Tools.zip). _Python 2.7 reached the end of its life on January 1st, 2020. Please upgrade your Python as Python 2.7 is no longer maintained. pip 21.0 will drop support for Python 2.7 in January 2021. More details about Python 2 support in pip, can be found at https://pip.pypa.io/en/latest/development/release-process/#python-2-support._
1. Unzip the contents of `AGRC Geocode Tools.zip` to a directory on your computer and open the associated python toolbox in ArcGIS Pro/Desktop.

## Development

### Releasing

There is a `cut_release.py` CLI to bump and package releases.

1. Install dependencies: `pip install -e ".[release]"`
1. Cut a release with the CLI
   `python cut_release.py minor`
   - To see the full options of the CLI use `python cut_release.py --help`
1. Push the release commit to GitHub
   - `python cut_release.py publish`

### Testing

1. install a local editable module
   - `pip install -e ".[tests]"`
   - `pip install -e .` to install without the testing dependencies
1. run the tests with code coverage. (viewable in vscode with [coverage gutters](https://github.com/ryanluker/vscode-coverage-gutters))
   - `pytest`
   - `pwt` to run the tests continually in watch mode
