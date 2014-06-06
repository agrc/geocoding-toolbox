geocoding-addin
===============

## Geocode Table tool
GeocodeAddressTable.py 
- Implements the Geocode Table tool with the AGRC Multiple Address geocoding service.

ToolRunner.py 
- Collects parameters from the script tool user interface.
- Must be imported into the script tool through ArcCatalog before being distributed.

# Build and Install
Build.py
- Copies the AGRC Geocode Tools.tbx ArcGIS tool box, the tool box's dependencies and the install file to the project build directory.

Install.py
- Installs AGRC Geocode Tools.tbx dependencies to the site-packages directory for the python installation with which it was executed.


#More information:
http://gis.utah.gov/new-utah-geocoding-toolbox-for-arcgis-desktop-2/
