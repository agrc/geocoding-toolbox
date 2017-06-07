"""
Script tool for ArcGIS which geocodes a table of addresses and produces a new table of the results.

@author: kwalker
"""

import urllib
import json
import arcpy
import os
import time
import random

VERSION_NUMBER = "3.0.4"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/agrc/geocoding-toolbox/back-to-single/tool-version.json"
RATE_LIMIT_SECONDS = (0.1, 0.3)
UNIQUE_RUN = time.strftime("%Y%m%d%H%M%S")


def api_retry(api_call):
    """Retry and api call if calling method returns None."""
    def retry(*args, **kwargs):
        response = api_call(*args, **kwargs)
        back_off = 1
        while response is None and back_off <= 8:
            arcpy.AddMessage('Retry wait: {}'.format(back_off))
            time.sleep(back_off + random.random())
            response = api_call(*args, **kwargs)
            back_off += back_off
        return response
    return retry


@api_retry
def get_version(check_url):
    """Get current version number."""
    try:
        r = urllib.urlopen(check_url)
        response = json.load(r)
    except:
        return None
    if r.getcode() is 200:
        currentVersion = response['VERSION_NUMBER']
        return currentVersion
    else:
        return None


class Geocoder(object):
    """Geocode and address and check api keys."""

    _api_key = None
    _url_template = "http://api.mapserv.utah.gov/api/v1/geocode/{}/{}?{}"

    def __init__(self, api_key):
        """Constructor."""
        self._api_key = api_key

    def _formatJsonData(self, formattedAddresses):
        jsonArray = {"addresses": []}
        for address in formattedAddresses:
            jsonArray["addresses"].append({"id": address.id,
                                           "street": address.address,
                                           "zone": address.zone})

        return jsonArray

    @api_retry
    def isApiKeyValid(self):
        """Check api key against known address."""
        apiCheck_Url = "http://api.mapserv.utah.gov/api/v1/geocode/{}/{}?{}"
        params = urllib.urlencode({"apiKey": self._api_key})
        url = apiCheck_Url.format("270 E CENTER ST", "LINDON", params)
        try:
            r = urllib.urlopen(url)
            response = json.load(r)
        except:
            return None

        # check status code
        if r.getcode() >= 500:
            return None
        elif r.getcode() is not 200 or response["status"] is not 200:
            return "Error: " + str(response["message"])
        else:
            return "Api key is valid."

    @api_retry
    def locateAddress(self, formattedAddress, **kwargs):
        """Create URL from formatted address and send to api."""
        apiCheck_Url = "http://api.mapserv.utah.gov/api/v1/geocode/{}/{}?{}"
        params = urllib.urlencode({"apiKey": self._api_key, "pobox": "true"})
        url = apiCheck_Url.format(formattedAddress.address, formattedAddress.zone, params)
        try:
            r = urllib.urlopen(url)
            response = json.load(r)
        except:
            return None

        if r.getcode() >= 500:
            return None
        else:
            return response


class AddressResult(object):
    """
    Store the results of a single geocode.

    Also contains static methods for writing a list AddressResults to different formats.
    """

    outputFields = ("INID", "INADDR", "INZONE",
                    "MatchAddress", "Zone", "Score",
                    "XCoord", "YCoord", "Geocoder")
    outputFieldTypes = ["TEXT", "TEXT", "TEXT",
                        "TEXT", "TEXT", "FLOAT",
                        "DOUBLE", "DOUBLE", "TEXT"]
    outputTextLengths = [100, 200, 12,
                         200, 12, None,
                         None, None, 50]

    def __init__(self, idValue, inAddr, inZone, matchAddr, zone, score, x, y, geoCoder):
        """ctor."""
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
        """str."""
        return "{},{},{},{},{},{},{},{},{}".format(*self.get_fields())

    def get_fields(self):
        """Get fields in output table order."""
        return (self.id, self.inAddress, self.inZone,
                self.matchAddress, self.zone, self.score,
                self.matchX, self.matchY, self.geoCoder)

    def getResultRow(self):
        """Get tuple of fields for InsertCursor."""
        outRow = []
        for f in self.get_fields():
            if f == "":
                outRow.append(None)
            else:
                outRow.append(f)
        return outRow

    @staticmethod
    def addHeaderResultCSV(outputFilePath):
        """Add header to CSV."""
        with open(outputFilePath, "a") as outCSV:
            outCSV.write(",".join(AddressResult.outputFields))

    @staticmethod
    def appendResultCSV(addrResult, outputFilePath):
        """Append a result to CSV."""
        with open(outputFilePath, "a") as outCSV:
            outCSV.write("\n" + str(addrResult))


class AddressFormatter(object):
    """Address formating utility."""

    def __init__(self, idNum, inAddr, inZone):
        """Ctor."""
        self.id = idNum
        self.address = self._formatAddress(inAddr)
        self.zone = self._formatZone(inZone)

    def _formatAddress(self, inAddr):
        addrString = str(inAddr)
        formattedAddr = str(addrString.strip().replace("#", " ").replace('/', " ").replace("%", " "))

        for c in range(0, 31):
            formattedAddr = formattedAddr.replace(chr(c), " ")
        for c in range(33, 37):
            formattedAddr = formattedAddr.replace(chr(c), " ")

        formattedAddr = formattedAddr.replace(chr(38), "and")

        for c in range(39, 47):
            formattedAddr = formattedAddr.replace(chr(c), " ")
        for c in range(58, 64):
            formattedAddr = formattedAddr.replace(chr(c), " ")
        for c in range(91, 96):
            formattedAddr = formattedAddr.replace(chr(c), " ")
        for c in range(123, 255):
            formattedAddr = formattedAddr.replace(chr(c), " ")

        return formattedAddr

    def _formatZone(self, inZone):
        formattedZone = str(inZone)

        if formattedZone[:1] == "8":
            formattedZone = formattedZone.strip()[:5]

        return formattedZone

    def isValid(self):
        """Test for address validity after formatting."""
        if len(self.address.replace(" ", "")) == 0 or len(self.zone.replace(" ", "")) == 0:
            return False
        elif self.id is None or self.address == 'None' or self.zone == 'None':
            return False
        else:
            return True


class TableGeocoder(object):
    """
    Script tool user interface allows for.

    -table of addresses
    -Fields to use
    -Geocoder paramater
    """

    locatorMap = {"Address points and road centerlines (default)": "all",
                  "Road centerlines": "roadCenterlines",
                  "Address points": "addressPoints"}
    spatialRefMap = {"NAD 1983 UTM Zone 12N": 26912,
                     "NAD 1983 StatePlane Utah North(Meters)": 32142,
                     "NAD 1983 StatePlane Utah Central(Meters)": 32143,
                     "NAD 1983 StatePlane Utah South(Meters)": 32144,
                     "GCS WGS 1984": 4326}

    def __init__(self, apiKey, inputTable, idField, addressField, zoneField, locator, spatialRef, outputDir, outputFileName, outputGeodatabase):
        """ctor."""
        self._apiKey = apiKey
        self._inputTable = inputTable
        self._idField = idField
        self._addressField = addressField
        self._zoneField = zoneField
        self._locator = locator
        self._spatialRef = spatialRef
        self._outputDir = outputDir
        self._outputFileName = outputFileName
        self._outputGdb = outputGeodatabase

    #
    # Helper Functions
    #
    def _createOutputTable(self):
        """Create output table and add fields."""
        def _addFieldsToOutputTable(outputFullPath):
            fields = zip(AddressResult.outputFields, AddressResult.outputFieldTypes, AddressResult.outputTextLengths)
            for field in fields:
                name, fieldType, textLength = field
                arcpy.AddField_management(outputFullPath,
                                          name,
                                          fieldType,
                                          field_length=textLength)

        insertTable = arcpy.CreateTable_management(self._outputGdb,
                                                   self._outputFileName.replace(".csv", ""))[0]
        inputIdType = [f.type.lower() for f in arcpy.ListFields(self._inputTable) if f.name.lower() == self._idField.lower()][0]
        if inputIdType in ['oid', 'objectid', 'integer', 'smallinteger']:
            AddressResult.outputFieldTypes[0] = 'LONG'
            AddressResult.outputTextLengths[0] = None

        _addFieldsToOutputTable(insertTable)

        return insertTable

    def _HandleCurrentResult(self, addressResult, outputFullPath, outputCursor):
        """Handle appending a geocoded address to the output CSV."""
        currentResult = addressResult
        AddressResult.appendResultCSV(currentResult, outputFullPath)
        outputCursor.insertRow(addressResult.getResultRow())

    def _processMatch(self, coderResponse, formattedAddr, outputFullPath, outputCursor):
        """Handle an address that has been returned by the geocoder."""
        locatorErrorText = "Error: Locator error"
        addressId = formattedAddr.id
        # Locator response Error
        if coderResponse is None:
            print "!!!Exception!!!"
            arcpy.AddWarning("Address ID {} failed".format(addressId))
            # Handle bad response
            currentResult = AddressResult(addressId, "", "", locatorErrorText, "", "", "", "", "")
            self._HandleCurrentResult(currentResult, outputFullPath, outputCursor)
        else:
            if coderResponse["status"] == 404:
                # address not found error
                inputAddress = formattedAddr.address
                inputZone = formattedAddr.zone
                currentResult = AddressResult(addressId, inputAddress, inputZone,
                                              "Error: " + coderResponse["message"], "", "", "", "", "")
                self._HandleCurrentResult(currentResult, outputFullPath, outputCursor)
            # Matched address
            else:
                coderResult = coderResponse["result"]
                #: if address grid in zone remove it
                matchAddress = coderResult["matchAddress"]
                matchZone = coderResult["addressGrid"]

                if ',' in matchAddress:
                    matchAddress = coderResult["matchAddress"].split(",")[0]

                splitInputAddress = coderResult["inputAddress"].split(",")
                inputAddress = splitInputAddress[0]
                inputZone = ""
                if len(splitInputAddress) > 1:
                    inputZone = splitInputAddress[1]
                else:
                    inputZone = ""

                currentResult = AddressResult(addressId, inputAddress, inputZone,
                                              matchAddress, matchZone, coderResult["score"],
                                              coderResult["location"]["x"], coderResult["location"]["y"],
                                              coderResult["locator"])
                self._HandleCurrentResult(currentResult, outputFullPath, outputCursor)

    def start(self):
        """Entery point into geocoding process."""
        outputFullPath = os.path.join(self._outputDir, self._outputFileName)

        # Setup progress bar
        record_count = int(arcpy.GetCount_management(self._inputTable).getOutput(0))
        rowNum = 1  # Counts records and updates progress bar
        increment = int(record_count / 10.0)
        if increment < 1:
            increment = 1
        arcpy.SetProgressor("step", "Geocoder Table Progess".format(increment, self._inputTable),
                            0, record_count, increment)

        geocoder = Geocoder(self._apiKey)
        # Test api key before we get started
        apiKeyMessage = geocoder.isApiKeyValid()
        if apiKeyMessage is None:
            arcpy.AddError("Geocode service failed to respond on api key check")
            return
        elif "Error:" in apiKeyMessage:
            arcpy.AddError(apiKeyMessage)
            return
        else:
            arcpy.AddMessage(apiKeyMessage)

        arcpy.AddMessage("Begin Geocode.")
        AddressResult.addHeaderResultCSV(outputFullPath)
        insertTable = self._createOutputTable()
        sequentialBadRequests = 0
        with arcpy.da.SearchCursor(self._inputTable, [self._idField, self._addressField, self._zoneField]) as cursor, \
                arcpy.da.InsertCursor(insertTable, AddressResult.outputFields) as outCursor:
            for row in cursor:

                try:
                    inFormattedAddress = AddressFormatter(row[0], row[1], row[2])
                except UnicodeEncodeError:
                    currentResult = AddressResult(row[0], "", "",
                                                  "Error: Unicode special character encountered", "", "", "", "", "")
                    self._HandleCurrentResult(currentResult, outputFullPath, outCursor)

                # Check for major address format problems before sending to api
                if inFormattedAddress.isValid():
                    throttleTime = random.uniform(RATE_LIMIT_SECONDS[0], RATE_LIMIT_SECONDS[1])
                    time.sleep(throttleTime)
                    matchedAddress = geocoder.locateAddress(inFormattedAddress,
                                                            **{"spatialReference": self._spatialRef,
                                                                "locators": self._locator,
                                                                "pobox": True})

                    if matchedAddress is None:
                        sequentialBadRequests += 1
                        if sequentialBadRequests <= 5:
                            currentResult = AddressResult(row[0], "", "",
                                                          "Error: Geocode failed", "", "", "", "", "")
                            self._HandleCurrentResult(currentResult, outputFullPath, outCursor)
                        else:
                            error_msg = "Geocode Service Failed to respond{}"
                            if rowNum > 1:
                                error_msg = error_msg.format(
                                    "\n{} adresses completed\nCheck: {} for partial table".format(rowNum - 1,
                                                                                                  outputFullPath))
                            else:
                                error_msg = error_msg.format("")
                            arcpy.AddError(error_msg)

                            return

                        continue

                    self._processMatch(matchedAddress, inFormattedAddress, outputFullPath, outCursor)

                else:
                        currentResult = AddressResult(row[0], inFormattedAddress.address, inFormattedAddress.zone,
                                                      "Error: Address invalid or NULL fields", "", "", "", "", "")
                        self._HandleCurrentResult(currentResult, outputFullPath, outCursor)

                # Update progress bar
                if (rowNum % increment) == 1:
                    arcpy.SetProgressorPosition(rowNum)
                rowNum += 1
                sequentialBadRequests = 0


if __name__ == "__main__":
    apiKey = arcpy.GetParameterAsText(0)
    inputTable = arcpy.GetParameterAsText(1)
    idField = arcpy.GetParameterAsText(2)
    addressField = arcpy.GetParameterAsText(3)
    zoneField = arcpy.GetParameterAsText(4)
    locator = TableGeocoder.locatorMap[str(arcpy.GetParameterAsText(5))]
    spatialRef = TableGeocoder.spatialRefMap[str(arcpy.GetParameterAsText(6))]
    outputDir = arcpy.GetParameterAsText(7)
    outputFileName = "GeocodeResults_" + UNIQUE_RUN + ".csv"
    outputGeodatabase = arcpy.CreateFileGDB_management(outputDir, "GeocodeTool_" + UNIQUE_RUN + ".gdb")[0]
    arcpy.SetParameterAsText(8, os.path.join(outputGeodatabase, outputFileName.replace(".csv", "")))

    version = VERSION_NUMBER
    arcpy.AddMessage("Geocode Table Version " + version)
    currentVersion = get_version(VERSION_CHECK_URL)
    if currentVersion and VERSION_NUMBER != currentVersion:
        arcpy.AddWarning('Current version is: {}'.format(currentVersion))
        arcpy.AddWarning('Please download at: https://github.com/agrc/geocoding-toolbox/raw/master/AGRC Geocode Tools.tbx')
    Tool = TableGeocoder(apiKey,
                         inputTable,
                         idField,
                         addressField,
                         zoneField,
                         locator,
                         spatialRef,
                         outputDir,
                         outputFileName,
                         outputGeodatabase)
    Tool.start()
    arcpy.AddMessage("Geocode completed")
