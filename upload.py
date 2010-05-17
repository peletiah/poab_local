import cgi
from optparse import OptionParser
import ConfigParser
import cgitb
cgitb.enable()
import os
import string
import re
from lxml import etree
from xml.etree import ElementTree


form = cgi.FieldStorage()
logimgonly = form.getvalue('logimgonly','')
smallsize = form.getvalue('smallsize','')
fullsize = form.getvalue('fullsize','')
filepath = form.getvalue('filepath','')

#smallsize='on'
#filepath='/srv/trackdata/bydate/2009-12-12/'

os.system("/usr/bin/rsync -d "+filepath+" peletiah@benko.login.cx:"+filepath)
os.system("/usr/bin/rsync -d "+filepath+"/images/ peletiah@benko.login.cx:"+filepath+"/images/")
os.system("/usr/bin/rsync -r "+filepath+"/trackfile/ peletiah@benko.login.cx:"+filepath+"/trackfile/")
os.system("/usr/bin/rsync -r "+filepath[:-1]+"-contentfile.xml peletiah@benko.login.cx:"+filepath[:-1]+"-contentfile.xml")
try:
    if logimgonly=='on':
        print 'logimgonly=on'
        print filepath[:-1]+"-contentfile.xml"
        tree = etree.parse(filepath[:-1]+"-contentfile.xml")
        root = tree.getroot()
        images = root.getiterator("img")
        for image in images:
            if image.find('logphoto').text=='True':
                print image.find('logphoto').text
                imagename=image.find('name').text
                os.system("/usr/bin/rsync -ia "+filepath+"/images/sorted/990/"+imagename+" peletiah@benko.login.cx:"+filepath+"/images/sorted/990/")
    if smallsize=='on':
        os.system("/usr/bin/rsync -ria "+filepath+"/images/sorted/990/ peletiah@benko.login.cx:"+filepath+"/images/sorted/990/")

    if fullsize=='on':
        os.system("/usr/bin/rsync -ria "+filepath+"/images/sorted/ peletiah@benko.login.cx:"+filepath+"/images/sorted/")
    print "Done!"
except NameError:
    print "Error with name"
    pass   
