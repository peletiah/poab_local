#################################################################################
##
## winteclib.py - Classes and utility functions for the wintec tools.
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
## Python 2.5 or later:
## <http://www.python.org>
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
The winteclib module contains classes and utility functions for the wintec tools.
"""

# pylint: disable-msg=C0302

from math import atan2, degrees, radians, sin, cos, tan, atan, sqrt, pi

import datetime
import struct
import locale
import os
from pytz import FixedOffset, timezone as gettimezone, utc, open_resource, ZERO, _FixedOffset
import re
import StringIO
import sys
import time
import urllib2
import zipfile

VERSION = "2.1"
""" The wintec tools version. """

def __pytz_open_resource(name):
    """
    Monkeypatch wrapper for pytz.open_resource().
    The original method fails when called by executables created with py2exe.

    We catch the exception of the original method and try to extract the resource
    from the zip file included in our py2exe installation.
    """
    #pylint: disable-msg=C0103,W0142
    try:
        return __pytz_orig_open_resource(name)
    except IOError:
        zipfilename = os.path.join(os.path.split(os.path.dirname(__file__))[0], 'pytz.zip')
        if os.path.exists(zipfilename):
            z = zipfile.ZipFile(zipfilename)
            name_parts = name.lstrip('/').split('/')
            # We skip fhe name_parts validation as it already succeeded in __pytz_orig_open_resource()
            filename = str.join("/", ['pytz', 'zoneinfo'] + name_parts)
            return StringIO.StringIO(z.read(filename))
        else:
            raise

def __pytz_dst(self, _dt):
    """
    Monkeypatch replacement for pytz._FixedOffset.dst().
    The original method returns None which makes the FixedOffset timezones unusable for astimezone().

    @param _dt: Unused.
    """
    # pylint: disable-msg=C0103,W0613
    return ZERO

# Do the open_resource() monkeypatch if we run in a py2exe environment.
if os.path.split(os.path.dirname(__file__))[1] == "library.zip":
    #pylint: disable-msg=C0103
    __pytz_orig_open_resource = open_resource
    open_resource = __pytz_open_resource

# Always monkeypatch _FixedOffset.dst().
_FixedOffset.dst = __pytz_dst
        
# Detect console encoding and decoding for converting the comment string from and to unicode.
if sys.platform == 'win32':
    CONSOLE_INPUT_ENCODING = 'mbcs'
    CONSOLE_OUTPUT_ENCODING = getattr(sys.stdout, 'encoding')
    if CONSOLE_OUTPUT_ENCODING == None:
        CONSOLE_OUTPUT_ENCODING = locale.getdefaultlocale()[1]
else:
    CONSOLE_INPUT_ENCODING = locale.getdefaultlocale()[1] 
    CONSOLE_OUTPUT_ENCODING = locale.getdefaultlocale()[1]

DATETIME_FILENAME_TEMPLATE = '%Y%m%d_%H%M%S'
""" Date and time format template used for filenames. """

TIMEZONE_TEMPLATE = re.compile("^([+-]?)([0-9]{1,2}):([0-9]{2})$")
""" Regular expression to parse timezone argument string. """

SOFTWARE_VERSION = 1.0
""" Software version number. """

HARDWARE_VERSION = 1.0
""" Hardware version number. """

timezoneidcache = {} # pylint: disable-msg=C0103
""" A map of (latitude, longitude) and timezone id. """

# pylint: disable-msg=R0913,C0302

class IllegalStateException(Exception):
    """
    Exception class for illegal state.
    """
    pass

class Track:
    """
    This class represents a single tracklog.
    """

    def __init__(self, trackdata, trackdataStart, trackpointCount, trackDuration, trackLength, timezone, autotimezone):
        """
        Constructor.
        
        @param trackdata: The array of all trackdata in the TK file.
        @param trackdataStart: The index of beginning of the first trackpoint belonging to this track.
        @param trackpointCount: The count of trackpoints in this track.
        @param trackDuration: The track duration in seconds.
        @param trackLength: The track length in kilometers.
        """
        self.trackdataStart = trackdataStart
        self.trackpointCount = trackpointCount
        self.trackdata = trackdata
        self.trackDuration = trackDuration
        self.trackLength = trackLength
        self.timezone = timezone
        self.autotimezone = autotimezone
        self.autotimezoneresult = None

    def trackpoints(self):
        """
        A generator which iterates over the trackpoints in this track.
        
        @return: Next L{Trackpoint}.
        """
        trackpointNumber = 0
        while trackpointNumber < self.trackpointCount:
            trackpointStart = self.trackdataStart + (trackpointNumber * Trackpoint.TRACKPOINTLEN)
            yield Trackpoint(self.trackdata[trackpointStart:trackpointStart + Trackpoint.TRACKPOINTLEN])
            trackpointNumber = trackpointNumber + 1

    def getFirstPoint(self):
        """
        Get the first L{Trackpoint} of this track.
        
        @return: The first L{Trackpoint} of this track.
        """
        return Trackpoint(self.trackdata[self.trackdataStart:self.trackdataStart + Trackpoint.TRACKPOINTLEN])
    
    def getLastPoint(self):
        """
        Get the last L{Trackpoint} of this track.
        
        @return: The last L{Trackpoint} of this track.
        """
        trackpointStart = self.trackdataStart + ((self.trackpointCount - 1) * Trackpoint.TRACKPOINTLEN)
        return Trackpoint(self.trackdata[trackpointStart:trackpointStart + Trackpoint.TRACKPOINTLEN])

    def getPoint(self, pointNumber):
        """
        Get the requested L{Trackpoint} of this track.
        
        @param pointNumber: Number of the requested L{Trackpoint}.
        @return: The requested L{Trackpoint} of this track.
        """
        assert 0 <= pointNumber < self.trackpointCount
        trackpointStart = self.trackdataStart + (pointNumber * Trackpoint.TRACKPOINTLEN)
        return Trackpoint(self.trackdata[trackpointStart:trackpointStart + Trackpoint.TRACKPOINTLEN])

    def getTrackData(self):
        """
        Get the complete data of this track.
        
        @return: The complete data of this track.
        """
        return self.trackdata[self.trackdataStart:self.trackdataStart + self.trackpointCount * Trackpoint.TRACKPOINTLEN]

    def getPushPointCount(self):
        """
        Get the count of push points in this track.
        
        @return: The count of push points in this track.
        """
        count = 0
        for point in self.trackpoints():
            if point.isLogPoint():
                count += 1
        return count

    def getTrackPointCount(self):
        """
        Get the count of trackpoints in this track.
        
        @return: The count of trackpoints in this track.
        """
        return self.trackpointCount
    
    def getTrackDuration(self):
        """
        Get the duration of this track in seconds.
        
        @return: The duration of this track in seconds.
        """
        return self.trackDuration
    
    def getTrackLength(self):
        """
        Get the length of this track in kilometers.
        
        @return: The length of this track in kilometers.
        """
        return self.trackLength
    
    def getTimezone(self):
        """
        Get timezone.
        
        @return: The L{FixedOffset} object.
        """
        if self.autotimezone:
            if not self.autotimezoneresult:
                self.autotimezoneresult = determineTimezone(self.getFirstPoint())
            return self.autotimezoneresult
        else:
            return self.timezone

class Trackpoint:
    """
    This class represents a single tracklog.
    """

    TRACKPOINTLEN = 16
    """ The length of a trackpoint in bytes."""

    TRACKSTART = 0x01
    """ The byte mask indicating the first trackpoint of a track."""

    LOGPOINT = 0x02
    """ The byte mask indicating a push log trackpoint."""
    
    OVERSPEEDPOINT = 0x04
    """ The byte mask indicating a over speed trackpoint."""

    def __init__(self, trackpoint):
        """
        Constructor.

        @param trackpoint: The array with the trackpoint data.
        """
        self.trackpoint = trackpoint
        assert len(self.trackpoint)  == self.TRACKPOINTLEN

    def isTrackStart(self):
        """
        Test wether the point is the first trackpoint of the track.
        
        @return: True if the point is the first trackpoint; False otherwise.
        """
        return self.TRACKSTART == self.getType() & self.TRACKSTART

    def isLogPoint(self):
        """
        Test wether the point is a push log trackpoint.
        
        @return: True if the point is push log trackpoint; False otherwise.
        """
        return self.LOGPOINT == self.getType() & self.LOGPOINT

    def isOverSpeedPoint(self):
        """
        Test wether the point is a over speed trackpoint.
        
        @return: True if the point is over speed trackpoint; False otherwise.
        """
        return self.OVERSPEEDPOINT == self.getType() & self.OVERSPEEDPOINT

    def getType(self):
        """
        Get the type of the trackpoint.
        
        @return: The type of the trackpoint.
        """
        return struct.unpack('<H', self.trackpoint[0x00:0x02])[0]

    def getDateTimeField(self):
        """
        Get the date/time field of the trackpoint.
        Use L{convertToDateTime()} to convert the result in a datetime object.
        
        @return: The date/time field of the trackpoint.
        """
        return struct.unpack('<I', self.trackpoint[0x02:0x06])[0]

    def getLatitude(self):
        """
        Get the latitude of the trackpoint in decimal degrees.
        
        @return: The latitude of the trackpoint.
        """
        return struct.unpack('<i', self.trackpoint[0x06:0x0a])[0] / 10000000.0

    def getLongitude(self):
        """
        Get the longitude of the trackpoint in decimal degrees.
        
        @return: The longitude of the trackpoint.
        """
        return struct.unpack('<i', self.trackpoint[0x0a:0x0e])[0] / 10000000.0

    def getAltitude(self):
        """
        Get the altitude of the trackpoint in meters.
        
        @return: The altiude of the trackpoint.
        """
        return float(struct.unpack('<h', self.trackpoint[0x0e:0x10])[0])

    def getDateTime(self, timezone = utc):
        """
        Get the local date and time of the trackpoint as datetime object.
        
        @param timezone: The local timezone.
        @return: A datetime object with the local date and time of the trackpoint.
        """
        return self.convertToDateTime(self.getDateTimeField()).astimezone(timezone)

    def getDateTimeString(self, format = '%y%m%d_%H%M', timezone = utc):
        """
        Format the local date and time of the trackpoint as a string.
        
        @param format: A strftime format string.
        @param timezone: The local timezone.
        @return: A formatted string with the local date and time of the trackpoint.
        """
        return self.getDateTime(timezone).strftime(format)

    def convertToDateTime(self, dateTime):    
        """
        Convert the date/time field value returned by L{getDateTimeField()}to a python datetime object.
        @param dateTime: The date/time field value.
        @return: A datetime object.
        """
        second = (dateTime & int('00000000000000000000000000111111', 2))
        minute = (dateTime & int('00000000000000000000111111000000', 2)) >> 6
        hour   = (dateTime & int('00000000000000011111000000000000', 2)) >> 12
        day    = (dateTime & int('00000000001111100000000000000000', 2)) >> 17
        month  = (dateTime & int('00000011110000000000000000000000', 2)) >> 22
        year   = (dateTime & int('11111100000000000000000000000000', 2)) >> 26
        year = year + 2000
        return datetime.datetime(year, month, day, hour, minute, second, tzinfo = utc)

    def getTemperature(self):
        """
        Get the temperature of the trackpoint in degrees celsius.
        This value is only available in WSG1000 version 2.0 logs.
        
        @return: The temperature of the trackpoint.
        """
        value = (self.getType() & int('0000000001111100', 2)) >> 2
        return (2 * value) - 10 
    
    def getAirPressure(self):
        """
        Get the air pressure of the trackpoint in hectopascal.
        This value is only available in WSG1000 version 2.0 logs.
        
        @return: The air pressure of the trackpoint.
        """
        value = (self.getType() & int('1111111110000000', 2)) >> 7
        return value + 589

class TK1File:
    """
    This class represents a .tk1 tracklog file.
    
    A .tk1 file contains one or more tracklogs.
    """
    # pylint: disable-msg=R0904

    HEADERLEN = 0x0400
    """ The length in bytes of the TK1 header. """

    FILEMARKER = 'WintecLogFormat'
    """ The identification marker at the beginning of the TK1 file. """

    EXPORT_TIMESTAMP_FORMAT = "%Y_%m_%d_%H:%M:%S"
    """ The strftime format string for the export timestamp. """

    SECONDS_PER_DAY = 24 * 60 * 60
    """ Number of seconds in a day. """

    class FooterEntry:
        """
        The footer entry for a track of an TK1File.

        24 Bytes per track.
        0x00-0x03: tracknumber 
        0x04-0x07: Offset first track 
        0x08-0x0b: Trackpoint count
        0x0c-0x0f: Track duration in seconds
        0x10-0x17: Track length as double
        """

        """ The length in bytes of the TK1 footer entry. """
        FOOTERENTRYLEN = 24

        def __init__(self):
            """
            Constructor.
            """
            self.data = None
        
        def create(self, tracknumber, trackvalues):
            """
            Create a FooterEntry.
            
            @param tracknumber: The track number.
            @param trackvalues: The track values.
            """
            self.data = struct.pack('<i', tracknumber) + \
                        struct.pack('<i', trackvalues[0]) + \
                        struct.pack('<i', trackvalues[1]) + \
                        struct.pack('<i', trackvalues[2]) + \
                        struct.pack('<d', trackvalues[3])
            assert len(self.data) == self.FOOTERENTRYLEN

        def fill(self, footerdata):
            """
            Set the footer data.
            
            @param footerdata: The footer data as array of bytes.
            """
            self.data = footerdata
            assert len(self.data) == self.FOOTERENTRYLEN

        def getFooterTrackNumber(self):
            """
            Get the track number the footer represents.
            
            @return: The track number.
            """
            return struct.unpack('<i', self.data[0x00:0x04])[0]

        def getFooterTrackOffset(self):
            """
            Get the offset of the track in the track data array.
            
            @return: The track offset. 
            """
            return struct.unpack('<i', self.data[0x04:0x08])[0]

        def getFooterTrackpointCount(self):
            """
            Get the count of trackpoints in the track.
            
            @return: The count of trackpoints.
            """
            return struct.unpack('<i', self.data[0x08:0x0c])[0]

        def getFooterTrackDuration(self):
            """
            Get the duration of the track in seconds.
        
            @return: The duration of the track.
            """
            return struct.unpack('<i', self.data[0x0c:0x10])[0]

        def getFooterTrackLength(self):
            """
            Get the length of the track in kilometers.
        
            @return: The length of the track.
            """
            return struct.unpack('<d', self.data[0x10:0x18])[0]
        
        def getData(self):
            """
            Return the footer data as byte array.
            
            @return: The footer data.
            """
            return self.data

    def __init__(self):
        """
        Constructor.
        """
        self.header = None
        self.trackdata = None
        self.footer = None
        self.timezone = utc
        self.autotimezone = False
    
    def init(self, devicename, deviceinfo, deviceserial, trackdata, exporttimestamp = None):
        """
        Fill data from given values.
        
        @param devicename: The name of the gps device.
        @param deviceinfo: The information string of the gps device.
        @param deviceserial: The serial number of the gps device.
        @param trackdata: The trackdata as array of bytes.
        @param exporttimestamp: The date and time of the data export.
        """
        assert devicename != None
        assert deviceinfo != None
        assert deviceserial != None
        assert trackdata != None
        self.trackdata = trackdata
        tracks = self.parseTracklog()
        trackcount = len(tracks)
        logversion = guessLogVersion(self.trackdata)
        self.header = self.createHeader(logversion, devicename, deviceinfo, deviceserial, len(self.trackdata),
                                        trackcount, exporttimestamp)
        self.footer = self.createFooter(tracks)

    def read(self, fileHandle):
        """
        Fill data from .tk1 fileHandle content.
        
        @param fileHandle: The file handle of a .tk1 file.
        """
        tk1filedata = fileHandle.read()
        self.header = tk1filedata[:TK1File.HEADERLEN]
        assert len(self.header) == TK1File.HEADERLEN
        assert self.header[:len(TK1File.FILEMARKER)] == TK1File.FILEMARKER
        footerpos = self.getFooterPos()
        self.trackdata = tk1filedata[TK1File.HEADERLEN:footerpos]
        assert len(self.trackdata) == self.getTrackpointCount() * Trackpoint.TRACKPOINTLEN
        self.footer = tk1filedata[footerpos:]
        assert len(self.footer) == self.getTrackCount() * TK1File.FooterEntry.FOOTERENTRYLEN

    def write(self, fileHandle):
        """
        Write data as .tk1 file.
        
        @param fileHandle: The file handle of a writeable .tk1 file.
        """
        if self.header == None or self.trackdata == None or self.footer == None:
            raise IllegalStateException
        fileHandle.write(self.header)
        fileHandle.write(self.trackdata)
        fileHandle.write(self.footer)

    def getLogVersion(self):
        """
        Get the log version of the gps device as float.
        
        @return: The log version of the gps device.
        """
        return struct.unpack('<f', self.header[0x0010:0x0014])[0]

    def getDeviceName(self):
        """
        Get the name of the gps device as string.
        
        @return: The name of the gps device. 
        """
        return self.header[0x0028:0x003b].strip(chr(0))

    def getDeviceInfo(self):
        """
        Get the gps device information as string.
        
        @return: The gps device information. 
        """
        return self.header[0x003c:0x004f].strip(chr(0))

    def getDeviceSerial(self):
        """
        Get the serial number of the gps device as string.
        
        @return: The serial number of the gps device. 
        """
        return self.header[0x0050:0x005e].strip(chr(0))

    def getExportTimeString(self):
        """
        Get the date and time of the export as string.
        
        @return: The date and time of the export. 
        """
        return self.header[0x0078:0x008b].strip(chr(0))

    def getTrackpointCount(self):
        """
        Get the number of trackpoints.
        
        @return: The number of trackpoints.
        """
        return struct.unpack('<I', self.header[0x0020:0x0024])[0]

    def getFooterPos(self):
        """
        Get the beginning position of the footer data.
        
        @return: The beginning position of the footer data.
        """
        return struct.unpack('<I', self.header[0x008c:0x0090])[0]

    def getTrackCount(self):
        """
        Get the number of tracks.
        
        @return: The number of tracks.
        """
        return struct.unpack('<I', self.header[0x0090:0x0094])[0]

    def getFooterEntry(self, trackNumber):
        """
        Get the L{FooterEntry} for the given track.
        
        @param trackNumber: The number of the track.
        @return: The L{FooterEntry}.
        """
        assert trackNumber >= 0 , trackNumber <= self.getTrackCount()
        footerEntry = TK1File.FooterEntry()
        footerEntry.fill(self.footer[trackNumber * TK1File.FooterEntry.FOOTERENTRYLEN
                                     :(trackNumber + 1) * TK1File.FooterEntry.FOOTERENTRYLEN])
        assert len(footerEntry.getData()) == TK1File.FooterEntry.FOOTERENTRYLEN
        return footerEntry

    def getTrack(self, footerEntry):
        """
        Get the L{Track} represented by the given L{FooterEntry}.
        
        @param footerEntry: The L{FooterEntry}.
        @return: The L{Track}.
        """
        trackdataStart = footerEntry.getFooterTrackOffset() - TK1File.HEADERLEN
        return Track(self.trackdata, trackdataStart, footerEntry.getFooterTrackpointCount(),
                     footerEntry.getFooterTrackDuration(), footerEntry.getFooterTrackLength(), self.timezone,
                     self.autotimezone)

    def tracks(self):
        """
        A generator which iterates over the tracks.
        
        @return: Next L{Track}.
        """
        trackNumber = 0
        while trackNumber < self.getTrackCount():
            footerEntry = self.getFooterEntry(trackNumber)
            yield self.getTrack(footerEntry)
            trackNumber = trackNumber + 1

    def __str__(self):
        """
        Create string representation.
        
        @return: String with data representation.
        """
        trackCount = self.getTrackCount()
        s = "Track count: %i\n" % trackCount
        for footerCount in range(trackCount):
            s += "\nTrack %i:\n" % footerCount
            footerEntry = self.getFooterEntry(footerCount)
            trackdataStart = footerEntry.getFooterTrackOffset() - TK1File.HEADERLEN
            trackpointCount = footerEntry.getFooterTrackpointCount()
            firstTrackpoint = Trackpoint(self.trackdata[trackdataStart:trackdataStart + Trackpoint.TRACKPOINTLEN])
            s += "Data offset: 0x%0x\n" % trackdataStart
            s += "Trackpoint count: %i\n" % trackpointCount
            s += "Track start date: %s\n" % firstTrackpoint.getDateTimeString()
            s += "Duration: %s\n" % datetime.timedelta(seconds = footerEntry.getFooterTrackDuration()).__str__()
            s += "Length: %0.2fkm\n" % footerEntry.getFooterTrackLength()
        return s

    def getFirstTrackpoint(self):
        """
        Get the first L{Trackpoint} of the track data.
        
        @return: The first L{Trackpoint}.
        """
        return Trackpoint(self.trackdata[0:Trackpoint.TRACKPOINTLEN])
    
    def getLastTrackpoint(self):
        """
        Get the last L{Trackpoint} of the track data.
        
        @return: The last L{Trackpoint}.
        """
        return Trackpoint(self.trackdata[-Trackpoint.TRACKPOINTLEN:])

    def createFilename(self):
        """
        Create a canonical filename for this tracklog.
        
        The Name consists of the data and time of the first trackpoint, the date and time of the last trackpoint
        and the number of tracks in the tracklog.
        
        @return: Canonical file name as string.
        """
        return "%s-%s#%03i.tk1" % (self.getFirstTrackpoint().getDateTimeString(),
                                   self.getLastTrackpoint().getDateTimeString(),
                                   self.getTrackCount())

    def setTimezone(self, timezone):
        """
        Set timezone.
        
        @param timezone: A L{FixedOffset} object.
        """
        self.timezone = timezone
        
    def setAutotimezone(self, autotimezone):
        """
        Set autotimezone.
        
        @param autotimezone: Boolean.
        """
        self.autotimezone = autotimezone

    def createFooter(self, tracks):
        """
        Create the footer data as byte array.
        
        @param tracks: A dictionary the track footer data created by l{parseTracklog()}.
        @return the footer data.
        """
        footer = ''
        footerEntry = TK1File.FooterEntry()
        for key in tracks.keys():
            footerEntry.create(key, tracks[key])
            footer += footerEntry.getData()
        assert len(footer) == len(tracks) * TK1File.FooterEntry.FOOTERENTRYLEN
        return footer

    def createHeader(self, logversion, devicename, deviceinfo, deviceserial, trackdatalen, trackcount,
                     exportTimestamp = None):
        """
        Create the header data as byte array.
        
        @param logversion: The version of the log as float.
        @param devicename: The name of the gps device.
        @param deviceinfo: The gps device information.
        @param deviceserial: The serial number of the gps device.
        @param trackdatalen: The length of the trackdata.
        @param trackcount: The number of tracks.
        @param exportTimestamp: The date and time of the data export.
        """
        if exportTimestamp == None:
            exportTimestamp = time.strftime(TK1File.EXPORT_TIMESTAMP_FORMAT, time.localtime())
        trackpointcount = trackdatalen / Trackpoint.TRACKPOINTLEN
        footerpos = trackdatalen + TK1File.HEADERLEN
        header = TK1File.FILEMARKER + chr(0x00) + \
                 struct.pack('<f', logversion) + \
                 struct.pack('<f', SOFTWARE_VERSION) + \
                 struct.pack('<f', HARDWARE_VERSION) + \
                 chr(0x41) + chr(0xbf) + chr(0x10) + chr(0x00) + \
                 struct.pack('<i', trackpointcount) + \
                 chr(0x00) + chr(0x00) + chr(0x00) + chr(0x00) + \
                 devicename + fillBytes(chr(0), 20-len(devicename)) + \
                 deviceinfo + fillBytes(chr(0), 20-len(deviceinfo)) + \
                 deviceserial + fillBytes(chr(0), 40-len(deviceserial)) + \
                 exportTimestamp + chr(0) + \
                 struct.pack('<i', footerpos) + \
                 struct.pack('<i', trackcount) + \
                 fillBytes(chr(0), 876)
        assert len(header) == TK1File.HEADERLEN
        return header

    def parseTracklog(self):
        """
        Parse tracklog and calculate footer data.
        
        The result is a dictionary with the track number as key and a tupel as value.
        The tupel contains the following values:
        track start, trackpoint count, track duration, track distance.
        
        @return: A dictionary with track footer data.
        """
        dataPos = 0
        trackCount = 0
        trackPointCount = 0
        trackStartPos = TK1File.HEADERLEN
        trackStartDateTime = None
        trackDistance = float(0)
        previousPoint = None
        tracks = {}
        while dataPos < len(self.trackdata):
            trackpoint = Trackpoint(self.trackdata[dataPos:dataPos + Trackpoint.TRACKPOINTLEN])
            # The first trackpoint might not be marked with the trackstart flag.
            if trackpoint.isTrackStart() or dataPos == 0:
                if previousPoint != None:
                    trackDuration = previousPoint.getDateTime() - trackStartDateTime
                    tracks[trackCount-1] = (trackStartPos, trackPointCount,
                                            trackDuration.days * TK1File.SECONDS_PER_DAY + trackDuration.seconds,
                                            trackDistance)
                # Start of new Track
                trackPointCount = 0
                trackStartPos = dataPos + TK1File.HEADERLEN
                trackStartDateTime = trackpoint.getDateTime()
                trackDistance = float(0)
                previousPoint = None
                trackCount += 1
            if previousPoint:
                trackDistance += calculateVincentyDistance(previousPoint.getLatitude(), previousPoint.getLongitude(),
                                                           trackpoint.getLatitude(), trackpoint.getLongitude())[0]
            previousPoint = trackpoint
            trackPointCount += 1
            dataPos += Trackpoint.TRACKPOINTLEN
        if previousPoint != None:
            trackDuration = previousPoint.getDateTime() - trackStartDateTime
            tracks[trackCount-1] = (trackStartPos, trackPointCount,
                                    trackDuration.days * TK1File.SECONDS_PER_DAY + trackDuration.seconds, trackDistance)
        return tracks

class TK2File:
    """
    This class represents a .tk2 tracklog file.
    
    A .tk2 file contains only one tracklog and is created by splitting a .tk1 file into separate tracks.
    """

    #pylint: disable-msg=R0904

    HEADERLEN = 0x0400
    """ The length in bytes of the TK2 header. """

    FILEMARKER = 'WintecLogTk2'
    """ The identification marker at the beginning of the TK2 file. """

    def __init__(self):
        """
        Constructor.
        """
        self.header = None
        self.trackdata = None
    
    def init(self, devicename, deviceinfo, deviceserial, exporttimestring, trackdata, trackduration, tracklength,
             trackpushpointcount, comment, timezone):
        """
        Fill data from given values.
        
        @param devicename: The name of the gps device.
        @param deviceinfo: The information string of the gps device.
        @param deviceserial: The serial number of the gps device.
        @param exporttimestring: The date and time of the export.
        @param trackdata: The trackdata as array of bytes.
        @param trackduration: The duration of the track.
        @param tracklength: The length of the track.
        @param trackpushpointcount: The number of push points in the track.
        @param comment: A user comment string.
        @param timezone: The timezone.
        """
        assert devicename != None
        assert deviceinfo != None
        assert exporttimestring != None
        assert trackdata != None
        self.trackdata = trackdata
        logversion = guessLogVersion(self.trackdata)
        self.header = self.createHeader(logversion, devicename, deviceinfo, deviceserial, exporttimestring,
                                        len(self.trackdata), trackduration, tracklength, trackpushpointcount, comment,
                                        timezone)

    def read(self, fileHandle):
        """
        Fill data from .tk2 fileHandle content.
        
        @param fileHandle: The file handle of a .tk2 file.
        """
        tk2filedata = fileHandle.read()
        self.header = tk2filedata[:TK2File.HEADERLEN]
        assert len(self.header) == TK2File.HEADERLEN
        self.trackdata = tk2filedata[TK2File.HEADERLEN:]
        assert len(self.trackdata) == self.getTrackpointCount() * Trackpoint.TRACKPOINTLEN

    def write(self, fileHandle):
        """
        Write data as .tk2 file.
        
        @param fileHandle: The file handle of a writeable .tk2 file.
        """
        if self.header == None or self.trackdata == None:
            raise IllegalStateException
        fileHandle.write(self.header)
        fileHandle.write(self.trackdata)

    def getLogVersion(self):
        """
        Get the log version of the gps device as float.
        
        @return: The log version of the gps device.
        """
        return struct.unpack('<f', self.header[0x0010:0x0014])[0]

    def getDeviceName(self):
        """
        Get the name of the gps device as string.
        
        @return: The name of the gps device. 
        """
        return self.header[0x001e:0x0031].strip(chr(0))

    def getDeviceInfo(self):
        """
        Get the gps device information as string.
        
        @return: The gps device information. 
        """
        return self.header[0x0032:0x0045].strip(chr(0))

    def getDeviceSerial(self):
        """
        Get the serial number of the gps device as string.
        
        @return: The serial number of the gps device. 
        """
        return self.header[0x0046:0x0054].strip(chr(0))

    def getExportTimeString(self):
        """
        Get the date and time of the export as string.
        
        @return: The date and time of the export. 
        """
        return self.header[0x006E:0x0081].strip(chr(0))
    
    def getTimezone(self):
        """
        Get the timezone as L{FixedOffset}.
        
        @return: The timezone.
        """
        signum = -1 if struct.unpack("<b", self.header[0x01ae:0x01af])[0] == 0 else 1
        hours = struct.unpack("<b", self.header[0x01af:0x01b0])[0]
        minutes = struct.unpack("<b", self.header[0x01b0:0x01b1])[0]
        return FixedOffset(signum * hours * 60 + minutes)

    def formatTkTimezone(self, timezone):
        """
        Format value of L{FixedOffset} timezone object for TK2/TK3 header.
    
        @param timezone: Local timezone.
        @return: timezone header bytes.
        """
        minutes = 0 if timezone == utc else timezone._minutes # pylint: disable-msg=W0212
        timeZoneSignum = 1 if minutes >= 0 else 0
        hours, minutes = divmod(abs(minutes), 60)
        return chr(timeZoneSignum) + chr(hours) + chr(minutes)

    def getComment(self):
        """
        Get the user comment as string with output encoding for the console.
        
        @return: The user comment.
        """
        comment = self.header[0x0082:0x01ae]
        return unicode(comment,'utf-16').encode(CONSOLE_OUTPUT_ENCODING).strip(chr(0))

    def setComment(self, comment):
        """
        Set the user comment.
        
        @param comment: The user comment as string with input encoding of the console.
        """
        commentUnicode = unicode(comment[:150], CONSOLE_INPUT_ENCODING).encode('unicode_internal')
        header = self.header
        header = header[:0x0082] + commentUnicode + fillBytes(chr(0), 300-len(commentUnicode)) + header[0x01ae:]
        assert len(header) == TK2File.HEADERLEN
        self.header = header

    def setTimezone(self, timezone):
        """
        Set the timezone.
        
        @param timezone: The timezone.
        """
        header = self.header
        
        header = header[:0x01ae] + self.formatTkTimezone(timezone) + header[0x01b1:]
        assert len(header) == TK2File.HEADERLEN
        self.header = header

    def getTrackCount(self):
        """
        Get the number of tracks.
        
        @return: The number of tracks.
        """
        return 1

    def getTrackpointCount(self):
        """
        Get the number of trackpoints.
        
        @return: The number of trackpoints.
        """
        return struct.unpack('<i', self.header[0x01cc:0x01d0])[0]

    def getTrackTime(self):
        """
        Get the duration of the track in seconds.
    
        @return: The duration of the track.
        """
        return struct.unpack('<i', self.header[0x01d0:0x01d4])[0]

    def getTrackDistance(self):
        """
        Get the length of the track in kilometers.
    
        @return: The length of the track.
        """
        return struct.unpack('<i', self.header[0x01d4:0x01d8])[0]

    def getPushpointCount(self):
        """
        Get the count of push points in this track.
        
        @return: The count of push points in this track.
        """
        return struct.unpack('<i', self.header[0x01d8:0x01dc])[0]

    def getTrack(self):
        """
        Get the L{Track} of this log.
        
        @return: The L{Track}.
        """
        return Track(self.trackdata, 0, self.getTrackpointCount(), self.getTrackTime(),
                     self.getTrackDistance() / 1000.0, self.getTimezone(), False)

    def tracks(self):
        """
        Wrap the track of this log in an array. 
        
        @return: Array containing the track.
        """
        return [self.getTrack()]

    def __str__(self):
        """
        Create string representation.
        
        @return: String with data representation.
        """
        s = ''
        s += "Device name: %s\n" % self.getDeviceName()
        s += "Device info: %s\n" % self.getDeviceInfo()
        s += "Device serial: %s\n" % self.getDeviceSerial()
        s += "Export time: %s\n" % self.getExportTimeString()
        s += "User comment: %s\n" % self.getComment()
        s += "Trackpoint count: %i\n" % self.getTrackpointCount()
        s += "Track time: %i\n" % self.getTrackTime()
        s += "Track distance: %i\n" % self.getTrackDistance()
        s += "Pushpoint count: %i\n" % self.getPushpointCount()
        s += "Timezone: %s\n" % datetime.datetime(2000, 1, 1, 0, 0, 0, tzinfo = self.getTimezone()).strftime("%z")
        return s

    def getFirstTrackpoint(self):
        """
        Get the first L{Trackpoint} of the track data.
        
        @return: The first L{Trackpoint}.
        """
        return Trackpoint(self.trackdata[0:Trackpoint.TRACKPOINTLEN])
    
    def createFilename(self):
        """
        Create a canonical filename for this tracklog.
        
        The Name consists of the data and time of the first trackpoint.
        
        @return: Canonical file name as string.
        """
#        return "%s.tk2" % (self.getFirstTrackpoint().getDateTimeString(DATETIME_FILENAME_TEMPLATE, self.timezone))
        return "%s.tk2" % (self.getFirstTrackpoint().getDateTimeString(DATETIME_FILENAME_TEMPLATE))

    def createHeader(self, logversion, devicename, deviceinfo, deviceserial, exporttimestring, trackdatalen,
                     trackduration, tracklength, trackpushpointcount, comment, timezone):
        """
        Create the header data.
        
        @param logversion: The version of the log as float.
        @param devicename: The name of the gps device.
        @param deviceinfo: The gps device information.
        @param deviceserial: The serial number of the gps device.
        @param exporttimestring: The date and time of the export.
        @param trackdatalen: The length of the trackdata.
        @param trackduration: The duration of the track.
        @param tracklength: The length of the track.
        @param trackpushpointcount: The number of push points in the track.
        @param comment: A user comment string.
        @param timezone: The timezone.
        """
        # pylint: disable-msg=R0914
        trackpointcount = trackdatalen / Trackpoint.TRACKPOINTLEN
        commentUnicode = unicode(comment[:150], CONSOLE_INPUT_ENCODING).encode('unicode_internal')
        firstTrackpoint = Trackpoint(self.trackdata[0:Trackpoint.TRACKPOINTLEN])
        firstTrackpointDate = firstTrackpoint.getDateTime(timezone).strftime("%Y-%m-%dT%H:%M:%SZ%z")
        firstTrackpointDate = firstTrackpointDate[:-2] + ":" + firstTrackpointDate[-2:]
        header = TK2File.FILEMARKER + chr(0x00) + chr(0x00) + chr(0x00) + chr(0x00) + \
                 struct.pack('<f', logversion) + \
                 struct.pack('<f', SOFTWARE_VERSION) + \
                 struct.pack('<f', HARDWARE_VERSION) + \
                 chr(0x41) + chr(0xbf) + \
                 devicename + fillBytes(chr(0), 20-len(devicename)) + \
                 deviceinfo + fillBytes(chr(0), 20-len(deviceinfo)) + \
                 deviceserial + fillBytes(chr(0), 40-len(deviceserial)) + \
                 exporttimestring + fillBytes(chr(0), 20-len(exporttimestring)) + \
                 commentUnicode + fillBytes(chr(0), 300-len(commentUnicode)) + \
                 self.formatTkTimezone(timezone) + \
                 firstTrackpointDate + chr(0) + \
                 struct.pack('<i', trackpointcount) + \
                 struct.pack('<i', trackduration) + \
                 struct.pack('<i', tracklength) + \
                 struct.pack('<i', trackpushpointcount) + \
                 fillBytes(chr(0), 548)
        assert len(header) == TK2File.HEADERLEN
        return header

class TK3File(TK2File):
    """
    The .tk3 file is very similar to the .tk2 file, but the track does only contain push log points.
    """

    # pylint: disable-msg=R0904,R0921

    FILEMARKER = 'WintecLogTk3'
    """ The identification marker at the beginning of the TK3 file. """

    def __init__(self):
        """
        Constructor.
        """
        TK2File.__init__(self)

    def init(self, devicename, deviceinfo, exporttimestring, trackdata, comment, timezone = utc):
        """
        Fill data from given values.
        
        @param devicename: The name of the gps device.
        @param deviceinfo: The information string of the gps device.
        @param exporttimestring: The date and time of the export.
        @param trackdata: The trackdata as array of bytes.
        @param comment: A user comment string.
        @param timezone: The local timezone.
        """
        # pylint: disable-msg=W0221
        assert devicename != None
        assert deviceinfo != None
        assert exporttimestring != None
        assert trackdata != None
        self.trackdata = self.extractPushLogPoints(trackdata)
        logversion = guessLogVersion(self.trackdata)
        self.header = self.createHeader(logversion, devicename, deviceinfo, exporttimestring, len(self.trackdata),
                                        timezone, comment)

    def read(self, fileHandle):
        """
        Fill data from .tk3 file content.
        
        @param fileHandle: The file handle of a .tk3 file.
        """
        tk3filedata = fileHandle.read()
        self.header = tk3filedata[:TK3File.HEADERLEN]
        assert len(self.header) == TK3File.HEADERLEN
        self.trackdata = tk3filedata[TK3File.HEADERLEN:]
        assert len(self.trackdata) == self.getTrackpointCount() * Trackpoint.TRACKPOINTLEN

    def extractPushLogPoints(self, trackdata):
        """
        Extract push log pointes from the trackdata.
        
        @param trackdata: The trackdata.
        @return: The push log points.
        """
        logPoints = ""
        track = Track(trackdata, 0, len(trackdata) / Trackpoint.TRACKPOINTLEN, 0, 0, utc, False)
        for trackpoint in track.trackpoints():
            if trackpoint.isLogPoint():
                logPoints += trackpoint.trackpoint
        return logPoints

    def getTrackpointCount(self):
        """
        Get the number of trackpoints.
        
        @return: The number of trackpoints.
        """
        return struct.unpack('<i', self.header[0x01ed:0x01f1])[0]

    def getPushpointCount(self):
        """
        Get the count of push points in this track.
        
        @return: The count of push points in this track.
        """
        return self.getTrackpointCount()

    def getTrack(self):
        """
        Get the L{Track} of this log.
        
        @return: The L{Track}.
        """
        return Track(self.trackdata, 0, self.getTrackpointCount(), 0, 0, self.getTimezone(), False)

    def getTrackTime(self):
        """
        Get the duration of the track in seconds.
    
        Not implemented for TK3File.

        @raise NotImplementedError: This method is not implemented.
        """
        raise NotImplementedError()

    def getTrackDistance(self):
        """
        Get the length of the track in kilometers.
        
        Not implemented for TK3File.
    
        @raise NotImplementedError: This method is not implemented.
        """
        raise NotImplementedError()

    def createFilename(self):
        """
        Create a canonical filename for this tracklog.
        
        The Name consists of the data and time of the first trackpoint.
        
        @return: Canonical file name as string.
        """
#        return "%s.tk3" % (self.getFirstTrackpoint().getDateTimeString(DATETIME_FILENAME_TEMPLATE, self.timezone))
        return "%s.tk3" % (self.getFirstTrackpoint().getDateTimeString(DATETIME_FILENAME_TEMPLATE))

    def __str__(self):
        """
        Create string representation.
        
        @return: String with data representation.
        """
        s = ''
        s += "Device name: %s\n" % self.getDeviceName()
        s += "Device info: %s\n" % self.getDeviceInfo()
        s += "Device serial: %s\n" % self.getDeviceSerial()
        s += "Export time: %s\n" % self.getExportTimeString()
        s += "User comment: %s\n" % self.getComment()
        s += "Trackpoint count: %i\n" % self.getTrackpointCount()
        s += "Timezone: %s\n" % self.getTimezone()
        return s

    def createHeader(self, logversion, devicename, deviceinfo, exporttimestring, trackdatalen, timezone, comment):
        """
        Create the header data.
        
        @param logversion: The version of the log as float.
        @param devicename: The name of the gps device.
        @param deviceinfo: The gps device information.
        @param exporttimestring: The date and time of the export.
        @param trackdatalen: The length of the trackdata.
        @param timezone: The timezone.
        @param comment: A user comment string.
        """
        # pylint: disable-msg=W0221,R0914
        trackpointcount = trackdatalen / Trackpoint.TRACKPOINTLEN
        commentUnicode = unicode(comment[:150], CONSOLE_INPUT_ENCODING).encode('unicode_internal')
        firstTrackpoint = Trackpoint(self.trackdata[0:Trackpoint.TRACKPOINTLEN])
        lastTrackpoint = Trackpoint(self.trackdata[-Trackpoint.TRACKPOINTLEN:])
        firstTrackpointDate = firstTrackpoint.getDateTime(timezone).strftime("%Y-%m-%dT%H:%M:%SZ%z")
        firstTrackpointDate = firstTrackpointDate[:-2] + ":" + firstTrackpointDate[-2:]
        lastTrackpointDate = lastTrackpoint.getDateTime(timezone).strftime("%Y-%m-%dT%H:%M:%SZ%z")
        lastTrackpointDate = lastTrackpointDate[:-2] + ":" + lastTrackpointDate[-2:]

        header = TK3File.FILEMARKER + chr(0x00) + chr(0x00) + chr(0x00) + chr(0x00) + \
                 struct.pack('<f', logversion) + \
                 struct.pack('<f', SOFTWARE_VERSION) + \
                 struct.pack('<f', HARDWARE_VERSION) + \
                 chr(0x41) + chr(0xbf) + \
                 devicename + fillBytes(chr(0), 20-len(devicename)) + \
                 deviceinfo + fillBytes(chr(0), 20-len(deviceinfo)) + \
                 fillBytes(chr(0), 40) + \
                 exporttimestring + fillBytes(chr(0), 20-len(exporttimestring)) + \
                 commentUnicode + fillBytes(chr(0), 300-len(commentUnicode)) + \
                 self.formatTkTimezone(timezone) + \
                 firstTrackpointDate + \
                 chr(0x00) + chr(0x00) + chr(0x00) + chr(0x00) + \
                 lastTrackpointDate + \
                 chr(0x00) + chr(0x00) + chr(0x00) + chr(0x00) + \
                 struct.pack('<i', trackpointcount) + \
                 fillBytes(chr(0), 527)
        assert len(header) == TK3File.HEADERLEN
        return header

def readTKFile(fileName):
    """
    Read a wintec file (.TK1, .TK2 or .TK3) and return an object of the corresponding class.
    
    @param fileName: the name and path of the wintec file to read.
    @return: An object of TK1File, TK2File or TK3File depending of the file content;
             None in case of an error.
    """
    fileMarkerLen = 12
    fileTypes = {TK1File.FILEMARKER[:fileMarkerLen] : TK1File,
                 TK2File.FILEMARKER                 : TK2File,
                 TK3File.FILEMARKER                 : TK3File,}
    
    f = open(fileName, "rb")
    fileMarker = f.read(fileMarkerLen)
    try:
        fileClass = fileTypes[fileMarker]
    except KeyError:
        print "%s is not a valid TK file!" % fileName
        return None
    tkFile = fileClass()
    f.seek(0)
    tkFile.read(f)
    f.close()
    return tkFile

def createOutputFile(outputDir, filename, template, value, flags = "w"):
    """
    Create output file.
    
    If outputDir is None, the file is created in the current directory.
    If filename is None, the file name is created by applying value to template. 
    
    @param outputDir: The output directory.
    @param filename: The output file name.
    @param template: The file name template.
    @param value: The file name template value.
    @param flags: The file open mode flags.
    @return: An open writeable filehandle.
    """
    if not filename:
        filename = template % value
    if outputDir:
        filename = os.path.join(outputDir, filename) 
    #print 'Create %s' % filename
    return open(filename, flags)

def fillBytes(byte, count):
    """
    Create a string of bytes with the given length.
    
    @param byte: The byte to fill into the string.
    @param count: The length of the resulting string.
    @return: A string of bytes with the given length.
    """
    assert count >= 0
    return count * byte

def guessLogVersion(trackdata):
    """
    Determine log version.
    
    The log version 2.0 was introduced for WSG-1000 logs containing temperature and air pressure.
    The temperature overlaps with the over speed flag of log version 1.0, so we must ignore this bit when searching
    for a trackpoint with temperature/air pressure set.
    """
    dataPos = 0
    for dataPos in range(0, len(trackdata), Trackpoint.TRACKPOINTLEN):
        if Trackpoint(trackdata[dataPos:dataPos + Trackpoint.TRACKPOINTLEN]).getType() & int('1111111111111000', 2):
            return 2.0
    return 1.0

def getGeonamesTimezoneId(lat, lng):
    """
    Query geonames.org for the timzoneId of the given GPS coordinate.
    
    @param lat: The latitude.
    @param lng: The longitude.
    @return: The timezoneId of the given GPS coordinate as string.
    """
    result = urllib2.urlopen("http://ws.geonames.org/timezone?lat=%s&lng=%s" % (lat, lng)).read()
    return re.search("<timezoneId>([^<]*)</timezoneId>", result).group(1)

def determineTimezone(trackpoint):
    """
    Get the timezone as L{FixedOffset} for the GPS coordinate and time of the given L{Trackpoint}.

    We use geonames.org to determine the timezoneId of the given GPS coordinate and use the Olson tz database to
    calculate the timezone offset for the date and time of the L{Trackpoint}, taking daylight saving time into account.

    We use L{FixedOffset} instead of the location timezone, because the local time should match the time recorded
    by devices like cameras, which are unlikely to self-adjust their clock for DST. If the track happens to contain the
    point of the beginning or ending of the DST, the local time would jump; this doesn't happen with the L{FixedOffset}
    timezone as it ignores DST.
        
    @param trackpoint: The L{Trackpoint}.
    @return: Local timezone.
    """
    lat = trackpoint.getLatitude()
    lon = trackpoint.getLongitude()
    utctime = trackpoint.getDateTime()
    key = (lat, lon)
    if key not in timezoneidcache:
        zoneId = timezoneidcache[key] = getGeonamesTimezoneId(lat, lon)
    else:
        zoneId = timezoneidcache[key]
    localtime = utctime.astimezone(gettimezone(zoneId)).replace(tzinfo = utc) 
    diff = localtime - utctime
    seconds = diff.seconds if diff.days >= 0 else (-24 * 60 * 60) + diff.seconds
    return FixedOffset(seconds / 60) 

def parseTimezone(timezoneString):
    """
    Parse timezone string and create a L{FixedOffset} object.

    @param timezoneString: The timezone string.
    @return: Local timezone.
    """
    match = TIMEZONE_TEMPLATE.match(timezoneString)
    if match:
        offset = int(match.group(2)) * 60 + int(match.group(3))
        return FixedOffset(-1 * offset if match.group(1) == "-" else offset)
    else:
        return None
    
def calculateVincentyDistance(latitude1, longitude1, latitude2, longitude2):
    """
    Calculate the geodesic distance and the bearing between two points using the formula
    devised by Thaddeus Vincenty, with the accurate WGS-84 ellipsoidal model of the earth.
    
    The code was borrowed from the geopy project (http://exogen.case.edu/projects/geopy/).
    
    @param latitude1: Latitude of the first point.
    @param longitude1: Longitude of the first point.
    @param latitude2: Latitude of the second point.
    @param longitude2: Longitude of the second point.
    @return: Tupel of distance between points in kilometers and bearing in degrees.
    """
    # pylint: disable-msg=C0103,R0914

    lat1 = radians(latitude1)
    lat2 = radians(latitude2)
    lng1 = radians(longitude1)
    lng2 = radians(longitude2)

    # Parameters of the WGS-84 ellipsoid model
    major = 6378.137
    minor = 6356.7523142
    f = 1 / 298.257223563

    delta_lng = lng2 - lng1

    reduced_lat1 = atan((1 - f) * tan(lat1))
    reduced_lat2 = atan((1 - f) * tan(lat2))

    sin_reduced1, cos_reduced1 = sin(reduced_lat1), cos(reduced_lat1)
    sin_reduced2, cos_reduced2 = sin(reduced_lat2), cos(reduced_lat2)

    lambda_lng = delta_lng
    lambda_prime = 2 * pi

    iter_limit = 20

    while abs(lambda_lng - lambda_prime) > 10e-12 and iter_limit > 0:
        sin_lambda_lng, cos_lambda_lng = sin(lambda_lng), cos(lambda_lng)

        sin_sigma = sqrt((cos_reduced2 * sin_lambda_lng) ** 2 +
                         (cos_reduced1 * sin_reduced2 - sin_reduced1 *
                          cos_reduced2 * cos_lambda_lng) ** 2)

        if sin_sigma == 0:
            # Coincident points
            return 0, 0

        cos_sigma = (sin_reduced1 * sin_reduced2 +
                     cos_reduced1 * cos_reduced2 * cos_lambda_lng)

        sigma = atan2(sin_sigma, cos_sigma)

        sin_alpha = cos_reduced1 * cos_reduced2 * sin_lambda_lng / sin_sigma
        cos_sq_alpha = 1 - sin_alpha ** 2

        if cos_sq_alpha != 0:
            cos2_sigma_m = cos_sigma - 2 * (sin_reduced1 * sin_reduced2 /
                                            cos_sq_alpha)
        else:
            cos2_sigma_m = 0.0 # Equatorial line

        C = f / 16. * cos_sq_alpha * (4 + f * (4 - 3 * cos_sq_alpha))

        lambda_prime = lambda_lng
        lambda_lng = (delta_lng + (1 - C) * f * sin_alpha *
                      (sigma + C * sin_sigma *
                       (cos2_sigma_m + C * cos_sigma * 
                        (-1 + 2 * cos2_sigma_m ** 2))))
        iter_limit -= 1

    if iter_limit == 0:
        raise ValueError("Vincenty formula failed to converge!")

    u_sq = cos_sq_alpha * (major ** 2 - minor ** 2) / minor ** 2

    A = 1 + u_sq / 16384. * (4096 + u_sq * (-768 + u_sq *
                                            (320 - 175 * u_sq)))

    B = u_sq / 1024. * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))

    delta_sigma = (B * sin_sigma *
                   (cos2_sigma_m + B / 4. *
                    (cos_sigma * (-1 + 2 * cos2_sigma_m ** 2) -
                     B / 6. * cos2_sigma_m * (-3 + 4 * sin_sigma ** 2) *
                     (-3 + 4 * cos2_sigma_m ** 2))))

    s = minor * A * (sigma - delta_sigma)

    sin_lambda, cos_lambda = sin(lambda_lng), cos(lambda_lng)

    alpha_1 = atan2(cos_reduced2 * sin_lambda,
                    cos_reduced1 * sin_reduced2 -
                    sin_reduced1 * cos_reduced2 * cos_lambda)

    initial_bearing = (360 + degrees(alpha_1)) % 360

    return s, initial_bearing
