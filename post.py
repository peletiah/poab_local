import cgi
from optparse import OptionParser
import ConfigParser
import cgitb
cgitb.enable()

form = cgi.FieldStorage()
title = form.getvalue('title','')
logtext = form.getvalue('logtext','')
phototitle = form.getvalue('phototitle','')
photodescription = form.getvalue('photodescription','')
photoset = form.getvalue('photoset','')
filepath = form.getvalue('filepath','')
basepath=filepath.rsplit('/',2)[0]+'/'
datepath=filepath.rsplit('/',2)[1]
upload = form.getvalue('upload','')


####### Create a proper imagelist #########
i=1
imglist=list()
while i < 100:
	try:
		tempimg=form.getvalue('img'+str(i),'')
		if tempimg:
			imglist.append(tempimg)
		i=i+1
	except NameError:
		i=i+1

####### Create a proper taglist #########
j=1
taglist=list()
while j < 100:
	try:
		temptag=form.getvalue('tag'+str(j),'')
		if temptag:
			taglist.append(temptag)
		j=j+1
	except NameError:
		j=j+1


######### write to contentfile.xml #########
print "Content-type: text/html"
print 

xmlcontent='''<?xml version="1.0" encoding="UTF-8"?>
<content>
  <log>
    <topic><![CDATA['''+ str(title) +''']]></topic>
    <logtext><![CDATA['''+ str(logtext) + ''']]></logtext>
    <filepath><![CDATA['''+ filepath + ''']]></filepath>\n
    <phototitle><![CDATA['''+ phototitle + ''']]></phototitle>\n
    <photodescription><![CDATA['''+ photodescription + ''']]></photodescription>\n
    <photoset><![CDATA['''+ photoset + ''']]></photoset>\n'''

for img in imglist:
    xmlcontent=xmlcontent + '''    <img><![CDATA['''+ img + ''']]></img>\n'''

for tag in taglist:
    xmlcontent=xmlcontent + '''    <tag><![CDATA['''+ tag + ''']]></tag>\n'''
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
