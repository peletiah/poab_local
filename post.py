import cgi
from optparse import OptionParser
import ConfigParser
import cgitb
cgitb.enable()

form = cgi.FieldStorage()
title = form.getvalue('title','')
logtext = form.getvalue('logtext','')
trackfile = form.getvalue('trackfile','')
photoset = form.getvalue('photoset','')
filepath = form.getvalue('filepath','')
basepath=filepath.rsplit('/',2)[0]+'/'
datepath=filepath.rsplit('/',2)[1]
upload = form.getvalue('upload','')


####### Create a proper imagedict #########
i=1
j=1
imglist=dict()
while i < 100:
    try:
             tempimg=form.getvalue('img'+str(i),'')
	     if tempimg:
		imglist[j]=tempimg
	        j=j+1
             i=i+1
    except KeyError:
             i=i+1

######### write to contentfile.xml #########
print "Content-type: text/html"
print 

xmlcontent='''<?xml version="1.0" encoding="UTF-8"?>
<content>
  <log>
    <topic><![CDATA['''+ str(title) +''']]></topic>
    <logtext><![CDATA['''+ str(logtext) + ''']]></logtext>
    <filepath><![CDATA['''+ filepath + ''']]></filepath>\n
    <trackfile><![CDATA['''+ trackfile + ''']]></trackfile>\n
    <photoset><![CDATA['''+ photoset + ''']]></photoset>\n'''

i=1
for img in imglist:
    xmlcontent=xmlcontent + '''    <img><![CDATA['''+ str(imglist[i]) + ''']]></img>\n'''
xmlcontent=xmlcontent + '''</log>
</content>'''

xmlfile=open(basepath+datepath+'-contentfile.xml','w')
xmlfile.write(xmlcontent)
xmlfile.close()

######## upload to server ########

if upload == 'on':
	print 'yes, upload'
else:
	print 'off'
