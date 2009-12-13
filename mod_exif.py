#!/usr/bin/python2.5

import os

def copy_exif(nefpath,jpgpath,imagename):
        os.system("/usr/bin/exiftool -qq -overwrite_original -TagsFromFile "+nefpath+"/"+imagename.split(".")[0]+".NEF "+jpgpath+"/"+imagename.split(".")[0]+".jpg > /var/log/lighttpd/exiftool.log")
        

def resize_990(jpgpath,resizepath,imagename):
    os.system("/usr/bin/convert "+jpgpath+"/"+imagename.split(".")[0]+".jpg -resize 990 "+resizepath+"/"+imagename.split(".")[0]+".jpg")

def remove_orientation(jpgpath,imagename):
        os.system("/usr/bin/exiftool -qq -overwrite_original -Orientation= "+jpgpath+"/"+imagename.split(".")[0]+".jpg >> /var/log/lighttpd/exiftool.log")
 
