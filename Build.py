'''
Created on May 7, 2014

@author: kwalker
'''
import os, shutil, time

startTime = time.time()
currentTime = time.time()

srcDir = os.path.join(os.path.dirname(__file__), "TableGeocoder")
dstDir = os.path.join(os.path.dirname(__file__), r"build\AGRC_GeocodingTools")

if os.path.exists(dstDir):
    shutil.rmtree(dstDir)
    
os.mkdir(dstDir)

toolBox = "AGRC Geocode Tools.tbx"
shutil.copy(os.path.join(os.path.dirname(__file__), toolBox), os.path.join(dstDir, toolBox))

installer = "Install.py"
shutil.copy(os.path.join(os.path.dirname(__file__), installer), os.path.join(dstDir, installer))

scriptFiles = ["GeocodeAddressTable.py"]
for f in scriptFiles:
    shutil.copy(os.path.join(srcDir, f), os.path.join(dstDir, f))

print "Build Complete"
print
print "-- Remember to import script into tool --"
