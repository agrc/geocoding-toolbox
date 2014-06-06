'''
Script tool for ArcGIS which geocodes a table of addresses and produces a new table of the results.

@author: kwalker
'''

import urllib, urllib2, json, arcpy, os
from operator import attrgetter


class Geocoder(object):

    _api_key = None
    _url_template = "http://api.mapserv.utah.gov/api/v1/geocode/multiple?{}"

    def __init__(self, api_key):
        """
        Geocode and address and check api keys.
        """
        self._api_key = api_key
        
    def _formatJsonData(self, formattedAddresses):
        jsonArray = {"addresses":[]}
        for address in formattedAddresses:
            jsonArray["addresses"].append({"id": address.id, 
                                           "street": address.address, 
                                           "zone": address.zone})
        
        return jsonArray
    
    
    def isApiValid(self):
        apiCheck_Url = "http://api.mapserv.utah.gov/api/v1/geocode/{}/{}?{}"
        params = urllib.urlencode({"apiKey": self._api_key})
        url = apiCheck_Url.format("270 E CENTER ST", "LINDON", params)
        r = urllib.urlopen(url)
        try:
            response = json.load(r)
        except:
            return "Error: Service did not respond.";
        
        #print response
        if r.getcode() is not 200 or response["status"] is not 200:
            return "Error: " + str(response["message"])
        else:
            return "Api key is valid."
            

    def locateAddresses(self, formattedAddresses, **kwargs):
        """Returns a list of address that were matched."""
        try:
            kwargs["apiKey"] = self._api_key
            params = urllib.urlencode(kwargs)
            url = self._url_template.format(params)
            jsonAddresses = self._formatJsonData(formattedAddresses)
            print "Json addresses before request\n\t" + str(jsonAddresses)
            
            data = json.dumps(jsonAddresses)
            req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
            r = urllib2.urlopen(req)    
            response = json.load(r)
            result = response["result"]["addresses"]
        except:
            print "!!!!!!!!exception!!!!!!!!!!!!!"
            result = None

        if r.getcode() is not 200 or response["status"] is not 200:
            result = None

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
    def addHeaderResultCSV(outputFilePath):
        with open(outputFilePath, "a") as outCSV:
            outCSV.write("{},{},{},{},{},{},{},{},{}".format("OBJID", "INADDR", "INZONE", 
                                                      "MatchAddress", "Zone", "Score", 
                                                      "XCoord", "YCoord", "Geocoder" ))
    @staticmethod
    def appendResultCSV(addrResult, outputFilePath): 
        with open(outputFilePath, "a") as outCSV:
            outCSV.write("\n" + str(addrResult))

    
    @staticmethod
    def createResultCSV(addrResultList, outputFilePath):
        """Replaced by appending method"""
        with open(outputFilePath, "w") as outCSV:
            outCSV.write("{},{},{},{},{},{},{},{},{}".format("OBJID", "INADDR", "INZONE", 
                                                          "MatchAddress", "Zone", "Score", 
                                                          "XCoord", "YCoord", "Geocoder" ))
            for result in addrResultList:
                outCSV.write("\n" + str(result))
        
class AddressFormatter(object):
    
    def __init__(self, idNum, inAddr, inZone):
        self.id = idNum
        self.address = self._formatAddress(inAddr)
        self.zone = self._formatZone(inZone)
         
    def _formatAddress(self, inAddr):
        formattedAddr = str(inAddr.strip().replace("#",""))
        
        for c in range(0,31):
            formattedAddr = formattedAddr.replace(chr(c)," ")
        for c in range(33,37):
            formattedAddr = formattedAddr.replace(chr(c)," ")
        
        formattedAddr = formattedAddr.replace(chr(38),"and")
        
        for c in range(39,47):
            formattedAddr = formattedAddr.replace(chr(c)," ")
        for c in range(58,64):
            formattedAddr = formattedAddr.replace(chr(c)," ")
        for c in range(91,96):
            formattedAddr = formattedAddr.replace(chr(c)," ")
        for c in range(123,255):
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
        elif self.id == None or self.address == 'None' or self.zone == 'None':
            return False       
        else:
            return True
        


class TableGeocoder(object):
    """
    Script tool user interface allows for providing:
    -table of addresses
    -Fields to use
    -Geocoder paramater.
    """
    locatorMap = {"Address points and road centerlines (default)" : "all", 
                  "Road centerlines" : "roadCenterlines", 
                  "Address points" : "addressPoints"}
    spatialRefMap = {"NAD 1983 UTM Zone 12N" : 26912, 
              "NAD 1983 StatePlane Utah North(Meters)" : 32142, 
              "NAD 1983 StatePlane Utah Central(Meters)" : 32143, 
              "NAD 1983 StatePlane Utah South(Meters)" : 32144, 
              "GCS WGS 1984" : 4326}
    
    def __init__(self, apiKey, inputTable, idField, addressField, zoneField, locator, spatialRef, outputDir, outputFileName):

        self._apiKey  = apiKey
        self._inputTable = inputTable
        self._idField = idField
        self._addressField = addressField
        self._zoneField = zoneField
        self._locator = locator
        self._spatialRef = spatialRef
        self._outputDir = outputDir
        self._outputFileName = outputFileName
        
#      
#Helper Functions
#
    def _HandleCurrentResult(self, addressResult, resultList, outputFullPath):
        """-Handles appending a geocoded address to the output CSV.
        -resultList is passed in by refernce and altered in this function.""" 
        currentResult = addressResult
        AddressResult.appendResultCSV(currentResult, outputFullPath)
        resultList.append(currentResult)
              
    def _ProcessIntermedaite(self, intermediateList, resultList, matchAddresses, outputFullPath):
        """-Handles a group of addresses that has been returned by the geocoder.
            -Lists are passed in by refernce and altered in this function."""
        
        locatorErrorText = "Error: Locator error"
        #Locator response Error 
        if matchAddresses == None:
            minErrorId = min(intermediateList, key=attrgetter('id'))
            maxErrorId = max(intermediateList, key=attrgetter('id'))
            print "!!!Exception!!!"
            arcpy.AddMessage(format("Address ID's {} to {} failed", minErrorId, maxErrorId))
            #Append min and max id in geocode group
            currentResult = AddressResult(minErrorId, "", "", locatorErrorText + " r", "", "", "", "", "")
            self._HandleCurrentResult(currentResult, resultList, outputFullPath)
            
            currentResult = AddressResult(maxErrorId, "", "", locatorErrorText  + " r", "", "", "", "", "")
            self._HandleCurrentResult(currentResult, resultList, outputFullPath)
            
          
        else:
            for coderResult in matchAddresses:
                
                if "error" in coderResult:
                    #inputAddress is not in result sometimes for some reason?
                    #address not found error
                    if "inputAddress" not in coderResult and "id" in coderResult:
                        currentResult = AddressResult(coderResult["id"], "", "", 
                        "Error: " + coderResult["error"], "", "", "", "", "")
                        self._HandleCurrentResult(currentResult, resultList, outputFullPath)
                    #address not found error
                    else:
                        splitInputAddress = coderResult["inputAddress"].split(",")
                        inputAddress = splitInputAddress[0]
                        inputZone = splitInputAddress[1]
                        currentResult = AddressResult(coderResult["id"], inputAddress, inputZone, 
                                                   "Error: " + coderResult["error"], "", "", "", "", "")
                        self._HandleCurrentResult(currentResult, resultList, outputFullPath)
                #Matched address        
                else:
                    splitMatchAddress = coderResult["matchAddress"].split(",")
                    matchAddress = splitMatchAddress[0]
                    matchZone = splitMatchAddress[1]
                    splitInputAddress = coderResult["inputAddress"].split(",")
                    inputAddress = splitInputAddress[0]
                    inputZone = splitInputAddress[1]
                    currentResult = AddressResult(coderResult["id"], inputAddress, inputZone, 
                                               matchAddress, matchZone, coderResult["score"], 
                                               coderResult["location"]["x"], coderResult["location"]["y"], 
                                               coderResult["locator"])
                    self._HandleCurrentResult(currentResult, resultList, outputFullPath)
                        
    
    def start(self):     
        resultList = []
        outputFullPath = os.path.join(self._outputDir, self._outputFileName)
        
        #Setup progress bar
        record_count = int(arcpy.GetCount_management(self._inputTable).getOutput(0))
        rowNum = 1
        increment = int(record_count / 10.0)
        if increment < 1:
            increment = 1
        arcpy.SetProgressor("step", "Geocoder Table Progess".format(increment, self._inputTable), 
                            0, record_count, increment)
    
        geocoder = Geocoder(self._apiKey)
        #Test api key before we get started
        apiKeyMessage = geocoder.isApiValid()
        if "Error:" in apiKeyMessage:
            arcpy.AddError(apiKeyMessage)
            raise Exception("API key error.")
        else:
            arcpy.AddMessage(apiKeyMessage)
            
        arcpy.AddMessage("Begin Geocode.")
        AddressResult.addHeaderResultCSV(outputFullPath)
        i = 0#counts records and updates progress bar.
        intermediateList = []#list for storing current geocode group.
        with arcpy.da.SearchCursor(self._inputTable, [self._idField, self._addressField, self._zoneField]) as cursor:
            for row in cursor:
                i += 1
                #Update progress bar
                if (rowNum % increment) == 0:
                    arcpy.SetProgressorPosition(rowNum)
                rowNum += 1
                
                try:
                    inFormattedAddress = AddressFormatter(row[0], row[1], row[2])
                except UnicodeEncodeError:
                    currentResult = AddressResult(row[0], "", "", 
                                                  "Error: Unicode special character encountered", "", "", "", "", "")
                    self._HandleCurrentResult(currentResult, resultList, outputFullPath)
                
                #Handle badly formatted addresses    
                if inFormattedAddress.isValid():
                    intermediateList.append(inFormattedAddress)
                else:
                        currentResult = AddressResult(row[0], inFormattedAddress.address, inFormattedAddress.zone, 
                                                        "Error: Address invalid or NULL fields", "", "", "", "", "")
                        self._HandleCurrentResult(currentResult, resultList, outputFullPath)
                
                #Send addresses to geocoder in a group
                if len(intermediateList) == 50 or (i == record_count):
                    matchAddresses = geocoder.locateAddresses(intermediateList, **{"spatialReference": self._spatialRef, "locators": self._locator})
                    self._ProcessIntermedaite(intermediateList, resultList, matchAddresses, outputFullPath)    
                    intermediateList = []
       
        #Create dbf table from the csv at the end. This table will automatically be added to TOC when run in arcmap.
        arcpy.CopyRows_management(os.path.join(self._outputDir, self._outputFileName), os.path.join(self._outputDir, self._outputFileName.replace(".csv", ".dbf")))