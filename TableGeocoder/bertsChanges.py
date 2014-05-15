'''
Created on Dec 13, 2013

@author: kwalker
'''

import urllib, json, arcpy, os
from time import strftime


class Geocoder(object):

    _api_key = None
    _url_template = "http://api.mapserv.utah.gov/api/v1/geocode/{}/{}?{}"

    def __init__(self, api_key):
        """
        Create your api key at
        https://developer.mapserv.utah.gov/secure/KeyManagement
        """
        self._api_key = api_key
    
    
    def isApiValid(self):
        params = urllib.urlencode({"apiKey": self._api_key})
        url = self._url_template.format("677 N SR 6", "DELta", params)
        r = urllib.urlopen(url)
        response = json.load(r)
        print response
        if r.getcode() is not 200 or response["status"] is not 200:
            return not ("API key." in str(response["message"]))
        else:
            return True
            

    def locateAddresses(self, street, zone, **kwargs):
        kwargs["apiKey"] = self._api_key
        params = urllib.urlencode(kwargs)
        
        url = self._url_template.format(street, zone, params)
        r = urllib.urlopen(url)

        response = json.load(r)

        if r.getcode() is not 200 or response["status"] is not 200:
            #print "{} {} was not found. {}".format(street, zone, response["message"])
            return None

        result = response["result"]

        #print "match: {} score [{}]".format(result["score"], result["matchAddress"])
        return result
    
class AddressResult(object):
    """Stores the results of a single geocode. Also contains static methods for writing a list
    AddressResults to different formats."""
  
    def __init__(self, idValue, inAddr, inZone, matchAddr, zone, score, x, y, geoCoder):
        self.id = idValue
        self.inAddress = inAddr
        self.inZone = inZone
        self.matchAddress = matchAddr
        self.zone = zone
        self.score = score
        self.matchX = x
        self.matchY = y
        self.geoCoder = geoCoder
    
    def __str__(self):
        return "{},{},{},{},{},{},{},{},{}".format(self.id, self.inAddress, self.inZone, 
                                       self.matchAddress, self.zone, self.score, 
                                       self.matchX, self.matchY, self.geoCoder)
    
    @staticmethod
    def createResultCSV(addrResultList, outputFilePath):
        with open(outputFilePath, "w") as outCSV:
            outCSV.write("{},{},{},{},{},{},{},{},{}".format("OBJID", "INADDR", "INZONE", 
                                                          "MatchAddress", "Zone", "Score", 
                                                          "XCoord", "YCoord", "Geocoder" ))
            for result in addrResultList:
                outCSV.write("\n" + str(result))
        
class AddressFormatter(object):
    
    def __init__(self, inAddr, inZone):
        self.address = self._formatAddress(inAddr)
        self.zone = self._formatZone(inZone)
         
    def _formatAddress(self, inAddr):
        formattedAddr = str(inAddr.strip().replace("#",""))
        
        for c in range(0,31):
            formattedAddr = formattedAddr.replace(chr(c)," ")
        for c in range(33,37):
            formattedAddr = formattedAddr.replace(chr(c)," ")
        for c in range(39-47):
            formattedAddr = formattedAddr.replace(chr(c)," ")
        for c in range(58-64):
            formattedAddr = formattedAddr.replace(chr(c)," ")
        for c in range(91-96):
            formattedAddr = formattedAddr.replace(chr(c)," ")
        for c in range(123-255):
            formattedAddr = formattedAddr.replace(chr(c)," ")         
        
        return formattedAddr
    
    def _formatZone(self, inZone):
        formattedZone = str(inZone)
        
        if formattedZone[:1] == "8":
            formattedZone = formattedZone.strip()[:5]        
        
        return formattedZone
    
    def isValid(self):
        if len(self.address.replace(" ","")) == 0 or len(self.zone.replace(" ","")) == 0:
            return False
        else:
            return True

if __name__ == "__main__":
    """
    Usage: Example usage is below. The dictionary passed in with ** can be any of the
    optional parameters for the api.
    """
    locatorMap = {"Address points and road centerlines (default)" : "all", "Road centerlines" : "roadCenterlines", "Address points" : "addressPoints"}
    
    apiKey  = arcpy.GetParameterAsText(0)
    inputTable = arcpy.GetParameterAsText(1)
    idField = arcpy.GetParameterAsText(2)
    addressField = arcpy.GetParameterAsText(3)
    zoneField = arcpy.GetParameterAsText(4)
    locator = locatorMap[str(arcpy.GetParameterAsText(5))]
    outputDir = arcpy.GetParameterAsText(6)
    outputFileName = "mapservGeocodeResults_" + strftime("%Y%m%d%H%M%S") + ".csv"
    
    testing = False
    if testing:
        apiKey = ""
        inputTable = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\GeocoderTools\TableGeocoder\Data\TestData.gdb\AddressTable"
        idField = "OBJECTID"
        addressField = "ADDRESS"
        zoneField = "zone"
        locator = "roadCenterlines"
        outputDir = r"C:\Users\Administrator\My Documents\Aptana Studio 3 Workspace\GeocoderTools\TableGeocoder\Data\TestOutput"
        outputFileName =  "mapservGeocodeResults_" + strftime("%Y%m%d%H%M%S") + ".csv"
    
    resultList = []
    arcpy.AddMessage("Version 1.0.3")
    
    geocoder = Geocoder(apiKey)
    if not geocoder.isApiValid():
        arcpy.AddError("API key is invalid")
        raise Exception("API key error")
    
    with arcpy.da.SearchCursor(inputTable, [idField, addressField, zoneField]) as cursor:
        for row in cursor:
            inFormattedAddress = AddressFormatter(row[1], row[2])
            
            if inFormattedAddress.isValid():
                coderResult = geocoder.locateAddresses(inFormattedAddress.address, inFormattedAddress.zone, **{"spatialReference": 26912, "locators": locator})#NAD 1983 UTM WKID
                
                if not (coderResult == None):
                    splitMatchAddress = coderResult["matchAddress"].split(",")
                    matchAddress = splitMatchAddress[0]
                    matchZone = splitMatchAddress[1]
                    resultList.append(AddressResult(row[0], inFormattedAddress.address, inFormattedAddress.zone, 
                                               matchAddress, matchZone, coderResult["score"], 
                                               coderResult["location"]["x"], coderResult["location"]["y"], coderResult["locator"]))
                else:
                    resultList.append(AddressResult(row[0], inFormattedAddress.address, inFormattedAddress.zone, 
                                                    "", "", "", "", "", ""))
                    
            else:
                resultList.append(AddressResult(row[0], inFormattedAddress.address, inFormattedAddress.zone, 
                                                    "", "", "", "", "", ""))
                                             
    print
    for r in resultList:
        print r   
    AddressResult.createResultCSV(resultList, os.path.join(outputDir, outputFileName))
    arcpy.CopyRows_management(os.path.join(outputDir, outputFileName), os.path.join(outputDir, outputFileName.replace(".csv", ".dbf")))
    arcpy.SetParameterAsText(6, os.path.join(outputDir, outputFileName.replace(".csv", ".dbf")))
    
    arcpy.AddMessage("Completed")


