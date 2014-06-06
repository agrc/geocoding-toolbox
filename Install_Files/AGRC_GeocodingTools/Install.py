'''
Created on May 7, 2014

@author: kwalker
'''
import os, shutil, time
from distutils.sysconfig import get_python_lib

try:
    srcDir = os.path.dirname(__file__)
    dstDir = get_python_lib()
    scriptFiles = ["GeocodeAddressTable.py"]
    for f in scriptFiles:
        shutil.copy(os.path.join(srcDir, f), os.path.join(dstDir, f))
        
    print "Files installed"
    
except:
    print "Error during installation"


#Show the message for a second.
startTime = time.time()
currentTime = time.time()
while currentTime - startTime < 1.5:
    currentTime = time.time()
