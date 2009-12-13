import cgi
from optparse import OptionParser
import ConfigParser
import cgitb
cgitb.enable()
import os
import string
import re

form = cgi.FieldStorage()
smallsize = form.getvalue('smallsize','')
fullsize = form.getvalue('fullsize','')
filepath = form.getvalue('filepath','')

os.system("/usr/bin/rsync -d "+filepath+" peletiah@benko.login.cx:"+filepath)
os.system("/usr/bin/rsync -d "+filepath+"/images/ peletiah@benko.login.cx:"+filepath+"/images/")
os.system("/usr/bin/rsync -r "+filepath+"/trackfile/ peletiah@benko.login.cx:"+filepath+"/trackfile/")
os.system("/usr/bin/rsync -r "+filepath[:-1]+"-contentfile.xml peletiah@benko.login.cx:"+filepath[:-1]+"-contentfile.xml")

if smallsize=='on':
    os.system("/usr/bin/rsync -r "+filepath+"/images/best_990/ peletiah@benko.login.cx:"+filepath+"/images/best_990/")

if fullsize=='on':
    os.system("/usr/bin/rsync -r "+filepath+"/images/best/ peletiah@benko.login.cx:"+filepath+"/images/best/")


print "Done!"
    
