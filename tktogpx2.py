#################################################################################
##
## tktogps.py - Convert gps tracklogs from Wintec TK file into a single GPS eXchange file.
##
## Copyright (c) 2008 Steffen Siebert <siebert@steffensiebert.de>
##
#################################################################################
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
##
#################################################################################
## Requirements                                                                ##
#################################################################################
##
## Python 2.2 or later:
## <http://www.python.org>
##
#################################################################################
## Program information:                                                        ##
#################################################################################
##
## - The file name of the created gpx file contains the date and time of the
##   first trackpoint in the TK file.
##
#################################################################################
## Support                                                                     ##
#################################################################################
##
## The latest version of the wintec tools is always available from my homepage:
## <http://www.SteffenSiebert.de/soft/python/wintec_tools.html>
##
## If you have bug reports, patches or some questions, just send a mail to
## <wintec_tools@SteffenSiebert.de>
##
#################################################################################

"""
Convert gps tracklogs from Wintec TK file into a single GPS eXchange file.
"""

from datetime import datetime
import getopt
from glob import glob
import os
import sys

from winteclib import VERSION, DATETIME_FILENAME_TEMPLATE, readTKFile, calculateVincentyDistance, createOutputFile, \
    parseTimezone, TK1File

# pylint: disable-msg=C0301

XML_HEADER = \
"""<?xml version="1.0" encoding="UTF-8"?>
<gpx
 version = "1.1"
creator = "tktogpx.py - http://www.steffensiebert.de/soft/python/wintec_tools.html"
xmlns:xsi = "http://www.w3.org/2001/XMLSchema-instance"
xmlns = "http://www.topografix.com/GPX/1/1"
xsi:schemaLocation = "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.topografix.com/GPX/gpx_overlay/0/3 http://www.topografix.com/GPX/gpx_overlay/0/3/gpx_overlay.xsd http://www.topografix.com/GPX/gpx_modified/0/1 http://www.topografix.com/GPX/gpx_modified/0/1/gpx_modified.xsd">
"""
""" XML header. """

METADATA = \
"""<metadata>
<bounds maxlat="%(maxlat).6f" maxlon="%(maxlon).6f" minlat="%(minlat).6f" minlon="%(minlon).6f"/>
</metadata>
"""
""" Metadata template. """

WAYPOINT = \
"""<wpt lat="%(lat).6f" lon="%(lon).6f">
 <ele>%(ele).6f</ele>
 <time>%(datetime)s</time>
 <name>Push Log Point #%(pushpoint)i</name>
 <desc>Lat.=%(lat).7f, Long.=%(lon).7f, Alt.=%(ele)im, Speed=%(speed)iKm/h, Course=%(bearing)ideg%(timezone)s.</desc>
 <sym>Waypoint</sym>
 <type>Other</type>
<extensions>
<label xmlns="http://www.topografix.com/GPX/gpx_overlay/0/3">
<label_text>Push Log Point #%(pushpoint)i</label_text>
</label>%(temppressure)s
</extensions>
</wpt>
"""
""" Waypoint template. """

TRACK_HEADER = \
"""<trk>
<name>Track %(track)03i</name>
 <desc>Total Track Points: %(trackpoints)i. Total time: %(hours)ih%(minutes)im%(seconds)is. Journey: %(distance).3fKm</desc>
<trkseg>
"""
""" Track header template. """

FIRST_TRACKPOINT = \
"""<trkpt lat="%(lat).7f" lon="%(lon).7f">
 <ele>%(ele).6f</ele>
 <time>%(datetime)s</time>
 <desc>Lat.=%(lat).7f, Long.=%(lon).7f, Alt.=%(ele)im%(timezone)s.</desc>
<extensions>%(temppressure)s
</extensions>
</trkpt>
"""
""" Template for first trackpoint. """

TRACKPOINT = \
"""<trkpt lat="%(lat).7f" lon="%(lon).7f">
 <ele>%(ele).6f</ele>
 <time>%(datetime)s</time>
 <desc>Lat.=%(lat).7f, Long.=%(lon).7f, Alt.=%(ele)im, Speed=%(speed)iKm/h, Course=%(bearing)ideg%(timezone)s.</desc>
<extensions>%(temppressure)s
</extensions>
</trkpt>
"""
""" Template for further trackpoints. """

TEMPERATURE_PRESSURE = """
<gpxx:%(extensiontype)sExtension xmlns:gpxx="http://gps.wintec.tw/xsd/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://gps.wintec.tw/xsd http://gps.wintec.tw/xsd/TMX_GpxExt.xsd">
<gpxx:Temperature>%(temperature)i</gpxx:Temperature>
<gpxx:Pressure>%(pressure)i</gpxx:Pressure>
</gpxx:%(extensiontype)sExtension>"""
""" Template for temperature and air pressure used for WSG1000 log version 2.0. """

TRACK_FOOTER = \
"""</trkseg>
</trk>
"""
""" Track footer. """

XML_FOOTER = \
"""</gpx>
"""
""" XML footer. """

def writeXmlHeader(outputFile):
    """
    Write XML Header.
    
    @param outputFile: the file to write to.
    """
    return outputFile.write(XML_HEADER)

def writeMetadata(tkfiles, outputFile):
    """
    Write metadata.
    
    @param tkfiles: A list of TK files with track data.
    @param outputFile: The file to write to.
    """
    maxLat = 0.0
    maxLon = 0.0
    minLat = None
    minLon = None
    for tkfile in tkfiles:
        for track in tkfile.tracks():
            for point in track.trackpoints():
                latitude = point.getLatitude()
                longitude = point.getLongitude()
                if latitude > maxLat:
                    maxLat = latitude
                
                if longitude > maxLon:
                    maxLon = longitude
                
                if latitude < minLat or minLat is None:
                    minLat = latitude
                
                if longitude < minLon or minLon is None:
                    minLon = longitude
                # FIXME: Time Machine X uses values higher than the maximum/lower than the minimum.
                #        I have no idea how these values are computed.

    values = {"minlat": minLat, "minlon": minLon, "maxlat": maxLat, "maxlon": maxLon}
    outputFile.write(METADATA % values)

def writeWaypoints(tkfiles, outputFile, usetimezone):
    """
    Write waypoints.
    
    @param tkfiles: A list of TK files with track data.
    @param outputFile: The file to write to.
    """
    # pylint: disable-msg=R0914
    pushPoint = 0
    for tkfile in tkfiles:
        previousPoint = None
        for track in tkfile.tracks():
            for point in track.trackpoints():
                if point.isLogPoint():
                    pushPoint = pushPoint + 1
                    speed = 0
                    bearing = 0
                    if previousPoint:
                        distance, bearing = calculateVincentyDistance(previousPoint.getLatitude(),
                                                                      previousPoint.getLongitude(),
                                                                      point.getLatitude(),
                                                                      point.getLongitude())
                        timedelta = point.getDateTime() - previousPoint.getDateTime()
                        time = timedelta.days * 24 * 60 * 60 + timedelta.seconds
                        if time != 0:
                            speed = distance / (time / float(60 * 60))
                    if tkfile.getLogVersion() != 2.0:
                        temppressure = ""
                    else:
                        temppressure = TEMPERATURE_PRESSURE % ({"extensiontype": "Waypoint",
                                                                "temperature": point.getTemperature(),
                                                                "pressure": point.getAirPressure()})
                    if usetimezone: 
                        timezone = datetime(2000, 1, 1, 0, 0, 0, tzinfo = track.getTimezone()).strftime(", TZ=%z")
                    else:
                        timezone = ""
                    values = {"lat": point.getLatitude(), "lon": point.getLongitude(),
                              "datetime": point.getDateTime().strftime('%Y-%m-%dT%H:%M:%SZ'), "pushpoint": pushPoint,
                              "ele": point.getAltitude(), "speed": speed, "bearing": bearing + 0.5,
                              "temppressure": temppressure, "timezone": timezone}
                    outputFile.write(WAYPOINT % values)
                
                previousPoint = point

def writeTracks(tkfiles, outputFile, usetimezone):
    """
    Write track data.
    
    @param tkfiles: A list of TK files with track data.
    @param outputFile: The file to write to.
    """
    # pylint: disable-msg=R0914
    trackNumber = 0
    for tkfile in tkfiles:
        for track in tkfile.tracks():
            previousPoint = None
            trackNumber += 1
            minutes, seconds = divmod(track.getTrackDuration(), 60)
            hours, minutes = divmod(minutes, 60)
            values = {"track": trackNumber, "trackpoints": track.getTrackPointCount(), "hours": hours,
                      "minutes": minutes, "seconds": seconds, "distance": track.getTrackLength()}
            outputFile.write(TRACK_HEADER % values)
            for point in track.trackpoints():
                speed = 0
                bearing = 0
                if previousPoint:
                    distance, bearing = calculateVincentyDistance(previousPoint.getLatitude(),
                                                                  previousPoint.getLongitude(),
                                                                  point.getLatitude(), point.getLongitude())
                    timedelta = point.getDateTime() - previousPoint.getDateTime()
                    time = timedelta.days * 24 * 60 * 60 + timedelta.seconds
                    if time != 0:
                        speed = distance / (time / float(60 * 60))
                if tkfile.getLogVersion() != 2.0:
                    temppressure = ""
                else:
                    temppressure = TEMPERATURE_PRESSURE % ({"extensiontype": "TrackPoint",
                                                            "temperature": point.getTemperature(),
                                                            "pressure": point.getAirPressure(),})
                if usetimezone: 
                    timezone = datetime(2000, 1, 1, 0, 0, 0, tzinfo = track.getTimezone()).strftime(", TZ=%z")
                else:
                    timezone = ""
                values = {"lat": point.getLatitude(), "lon": point.getLongitude(),
                          "datetime": point.getDateTime().strftime('%Y-%m-%dT%H:%M:%SZ'), "ele": point.getAltitude(),
                          "speed": speed, "bearing": bearing + 0.5, "temppressure": temppressure, "timezone": timezone}
                if previousPoint:
                    outputFile.write(TRACKPOINT % values)
                else:
                    outputFile.write(FIRST_TRACKPOINT % values)
                previousPoint = point
            outputFile.write(TRACK_FOOTER)

def writeXmlFooter(outputFile):
    """
    Write XML Footer.
    
    @param outputFile: the file to write to.
    """
    return outputFile.write(XML_FOOTER)

def createGpxFile(outputFile, tkfiles, usetimezone):
    """
    Create gpx file.
    
    @param outputFile: The gpx file handle.
    @param tkfiles: A list of TK files with track data.
    """
    writeXmlHeader(outputFile)
    writeMetadata(tkfiles, outputFile)
    writeWaypoints(tkfiles, outputFile, usetimezone)  
    writeTracks(tkfiles, outputFile, usetimezone)
    writeXmlFooter(outputFile)

def usage():
    """
    Print program usage.
    """
    executable = os.path.split(sys.argv[0])[1]
    print "%s Version %s (C) 2008 Steffen Siebert <siebert@steffensiebert.de>" % (executable, VERSION)
    print "Convert gps tracklogs from Wintec TK files into a single GPS eXchange file.\n"
    print "Usage: %s [-d outputdir] [-o filename] [-t +hh:mm|--autotz] <tk files>" % executable
    print "-d: Use output directory."
    print "-o: Use output filename."
    print "-t: .tk1: Use timezone for local time (offset to UTC). .tk2/.tk3: Use timezone stored in tk-file."
    print "--autotz: .tk1: Determine timezone from first trackpoint. .tk2/.tk3: Use timezone stored in tk-file."
    print
    print "Note: The time in .gpx files is defined as UTC. If you use the -t or --autotz option, the time is converted"
    print "to the timezone, but still marked as UTC. The used timezone is added to the <desc> tag."

def main():
    """
    The main method.
    """
    # pylint: disable-msg=R0912,R0914,R0915
    outputDir = None
    outputFile = None
    filename = None
    timezone = None
    autotimezone = False
    usetimezone = False
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "?hd:o:")
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    if len(args) == 0:
        usage()
        sys.exit(1)

    for o, a in opts:
        if o in ("-h", "-?"):
            usage()
            sys.exit()
        if o == "-d":
            outputDir = a
        if o == "-o":
            filename = a
        if o == "-t":
            timezone = parseTimezone(a)
            if timezone == None:
                print "Timzone string doesn't match pattern +hh:mm!"
                sys.exit(4)
            usetimezone = True
        if o == "--autotz":
            usetimezone = autotimezone = True

    if outputDir and not os.path.exists(outputDir):
        print "Output directory %s doesn't exist!" % outputDir
        sys.exit(3)

    tkfiles = []
    for arg in args:
        for tkFileName in glob(arg):
            tkfile = readTKFile(tkFileName)
            if isinstance(tkfile, TK1File):
                if timezone:
                    tkfile.setTimezone(timezone)
                tkfile.setAutotimezone(autotimezone)
            tkfiles.append(tkfile)

    tkfiles.sort(lambda x, y: cmp(x.getFirstTrackpoint().getDateTime(), y.getFirstTrackpoint().getDateTime()))
    
    try:
        if len(tkfiles) > 1:
            dateString = tkfiles[0].getFirstTrackpoint().getDateTimeString()
            dateString2 = tkfiles[-1].getFirstTrackpoint().getDateTimeString()
            outputFile = createOutputFile(outputDir, filename, '%s-%s#%03i.gpx', (dateString, dateString2,
                                                                                  len(tkfiles)))
        else:
            if isinstance(tkfiles[0], TK1File):
                dateString = tkfiles[0].getFirstTrackpoint().getDateTimeString()
                dateString2 = tkfiles[0].getLastTrackpoint().getDateTimeString()
                outputFile = createOutputFile(outputDir, filename, '%s-%s#%03i.gpx', (dateString, dateString2,
                                                                                      tkfiles[0].getTrackCount()))
            else:
                dateString = tkfiles[0].getFirstTrackpoint().getDateTimeString(DATETIME_FILENAME_TEMPLATE)
                outputFile = createOutputFile(outputDir, filename, '%s.gpx', dateString)
        if outputFile == None:
            return
        createGpxFile(outputFile, tkfiles, usetimezone)
    finally:
        if outputFile != None:
            outputFile.close()

def interactive(outputDir,filename,tkFileName):
    """
    The main method.
    """
    # pylint: disable-msg=R0912,R0914,R0915
    outputFile = None
    timezone = None
    autotimezone = False
    usetimezone = False
   
    if outputDir and not os.path.exists(outputDir):
        print "Output directory %s doesn't exist!" % outputDir
        sys.exit(3)

    tkfiles = []
    for tkFileName in glob(tkFileName):
        tkfile = readTKFile(tkFileName)
        if isinstance(tkfile, TK1File):
        	if timezone:
        	    tkfile.setTimezone(timezone)
    	tkfile.setAutotimezone(autotimezone)
        tkfiles.append(tkfile)



    tkfile = readTKFile(tkFileName)
    tkfiles.sort(lambda x, y: cmp(x.getFirstTrackpoint().getDateTime(), y.getFirstTrackpoint().getDateTime()))
    
    try:
        if len(tkfiles) > 1:
            dateString = tkfiles[0].getFirstTrackpoint().getDateTimeString()
            dateString2 = tkfiles[-1].getFirstTrackpoint().getDateTimeString()
            outputFile = createOutputFile(outputDir, filename, '%s-%s#%03i.gpx', (dateString, dateString2,
                                                                                  len(tkfiles)))
        else:
            if isinstance(tkfiles[0], TK1File):
                dateString = tkfiles[0].getFirstTrackpoint().getDateTimeString()
                dateString2 = tkfiles[0].getLastTrackpoint().getDateTimeString()
                outputFile = createOutputFile(outputDir, filename, '%s-%s#%03i.gpx', (dateString, dateString2,
                                                                                      tkfiles[0].getTrackCount()))
            else:
                dateString = tkfiles[0].getFirstTrackpoint().getDateTimeString(DATETIME_FILENAME_TEMPLATE)
                outputFile = createOutputFile(outputDir, filename, '%s.gpx', dateString)
        if outputFile == None:
            return
        createGpxFile(outputFile, tkfiles, usetimezone)
    finally:
        if outputFile != None:
            outputFile.close()
if __name__ == "__main__":
    main()
