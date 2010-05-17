import hashlib
import os
import tktogpx2
from optparse import OptionParser

parser = OptionParser()
#parser.add_option("-h", "--help", action="help")
parser.add_option("-r", action="store_true", dest="raw",
        help="Upload raw files(Lots of bandwith required)")
parser.add_option("-f", action="store_true", dest="fullsize",
        help="Upload fullsize (jpg) files")


(options, args) = parser.parse_args()
raw=options.raw
fullsize=options.fullsize

print fullsize
print raw

for path in os.listdir('/srv/trackdata/bydate/'):
    filetypes=('.xml')
    print path
    if path.lower().endswith(filetypes):
        pass
    else:
        datepath='/srv/trackdata/bydate/'+path+'/'
        trackpath=datepath+'trackfile/'
        print 'current directory is '+path
        for trackfile in os.listdir(trackpath):
            if trackfile.lower().endswith('.tk1'):
                #passes outputDir,gpx-filename and tkFileName to tk2togpx.interactive to convert the tk1 to gpx
                if os.path.exists(trackpath+trackfile[:-3]+'gpx'): # is there already a gpx-file with this name?
                    pass
                else:
                    tktogpx2.interactive(trackpath,trackfile.split('.')[0]+'.gpx',trackpath+trackfile)
            else:
                pass
#        os.system("/usr/bin/perl /var/www/gpsPhoto.pl --dir "+datepath+"images/sorted/ --delete-geotag")
#        os.system("/usr/bin/perl /var/www/gpsPhoto.pl --dir "+datepath+"images/sorted/ --gpsdir "+datepath+'trackfile'+" --timeoffset 0 --maxtimediff 1200")
    if raw == True:
        #upload raw(NEF)-Files too
        os.system("/usr/bin/rsync -ria --progress "+datepath+"images/ peletiah@benko.login.cx:"+datepath+"images/")
    if fullsize == True:
        #upload fullsize too
        os.system("/usr/bin/rsync -ria --progress "+datepath+"images/sorted/ peletiah@benko.login.cx:"+datepath+"images/sorted/")
    #upload files missing in resized-directory
    os.system("/usr/bin/rsync -ria --progress "+datepath+"images/sorted/990/ peletiah@benko.login.cx:"+datepath+"images/sorted/990/")
