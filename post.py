import cgi
from optparse import OptionParser
import ConfigParser
import cgitb
cgitb.enable()
from lxml import etree
from xml.etree import ElementTree
import os
import string
import re
from decimal import Decimal
import decimal
import time, datetime

form = cgi.FieldStorage()
title = form.getvalue('title','')
logtext = form.getvalue('logtext','')
phototitle = form.getvalue('phototitle','')
photoset = form.getvalue('photoset','')
filepath = form.getvalue('filepath','')
basepath=filepath.rsplit('/',2)[0]+'/'
datepath=filepath.rsplit('/',2)[1]
createdate=form.getvalue('createdate','')
upload = form.getvalue('upload','')

#img1="DSC_5843.jpg"
#description1="christian+%26+daniela"
#img2="dsc_4649.jpg"
#description2="komischer+nebel+2008"
#tag1="tag1"
#tag2="tag2"
#phototitle="Steiermark+November+2009"
#photoset="styria"
#filepath="/srv/trackdata/bydate/2009-12-05/"
#title="Hello+World"
#logtext="<div>asdfdsaffas</div><div>sadfadsfdsadf</div><div><br/></div>[img1]<div><br/></div><div><br/></div><div>sadfdsafdsa</div><div>dsafdsaf</div><div><br/></div><div>[img2]</div>"
#upload="on"


####### Create a proper imagelist #########
i=1
imgdict={}
while i < 100:
    tempimg=''
    desc=''
    try:
        #tempimg=img1
        tempimg=form.getvalue('img'+str(i),'')
        if tempimg:
            try:
                desc=form.getvalue('description'+str(i),'')
                #desc=description1
            except NameError:
                desc=''
            imgdict[tempimg]=desc
        i=i+1
    except NameError:
        i=i+1

####### Create a proper taglist #########
j=1
taglist=list()
while j < 100:
	try:
		temptag=form.getvalue('tag'+str(j),'')
		#temptag=tag1
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
    <photoset><![CDATA['''+ photoset + ''']]></photoset>\n
    <createdate><![CDATA['''+ createdate + ''']]></createdate>\n'''

i=0
for img in imgdict:
    xmlcontent=xmlcontent + '''    <img><![CDATA['''+ img + ''':''' + imgdict[img] + ''']]></img>\n'''

for tag in taglist:
    xmlcontent=xmlcontent + '''    <tag><![CDATA['''+ tag + ''']]></tag>\n'''
xmlcontent=xmlcontent + '''</log>
</content>'''

xmlfile=open(basepath+datepath+'-contentfile.xml','w')
xmlfile.write(xmlcontent)
xmlfile.close()


tree = etree.fromstring(file(basepath+datepath+'-contentfile.xml', "r").read())
topic =  (tree.xpath('//topic')[0]).text.replace("&gt;",">").replace("&lt;","<")
logtext =  (tree.xpath('//logtext')[0]).text.replace("&gt;",">").replace("&lt;","<")
filepath =  (tree.xpath('//filepath')[0]).text
photosetname =  (tree.xpath('//photoset')[0]).text
phototitle =  (tree.xpath('//phototitle')[0]).text
createdate =  (tree.xpath('//createdate')[0]).text
xmlimgdesc={}
xmlimglist=list()
xmltaglist=list()

query_xmlimglist='//img'
for img in tree.xpath(query_xmlimglist):
    image,description=img.text.split(':')
    xmlimgdesc[image]=description
    xmlimglist.append(image)
query_xmltaglist='//tag'
for element in tree.xpath(query_xmltaglist):
    xmltaglist.append(element.text)

i=1
for image in xmlimglist:
    logtext=logtext.replace('[img'+str(i)+']','<img src="/preview/'+filepath.split('/')[4]+"/images_sorted/"+image+'" class="resize">')
    i=i+1

print """
<html> 
    <head> 
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8"> 
    <title>Preview Log</title> 
    </head> 
    <body>
<link rel="stylesheet" type="text/css" href="/css/preview.css" media="screen">
<div id="content">
    <div id="log" "clearfix">
                <div id="logdetail">
                <table id="logheader">
                    <tbody>
                    <tr>
                        <td class="leftcol">""" + createdate + """</td>
                        <td class="rightcol">Waidhofen an der Thaya, Lower Austria, Austria</td>
                    </tr>
                    </tbody>
                </table>
                <div id="logcontent">
                <h2>""" + topic + """</h2>
                    <b>distance:</b> 100.10km<br>
                    <b>duration:</b> 2h 10min<br>
                <div id="logdetail_icons">
                <span class="image_icon"><a href="/view"></a></span>
                <span class="track_icon"><a href="/track/infomarker/14906"></a></span>
                <span class="stats_icon"><a href="/facts/stats"></a></span></div><br><br>
                """ + logtext + """
                </div>
            </div>
    </div>
<form action='edit.py'>
        <div id="edit">
            <input name='filepath' type='text' value='%s' size='50' />
            <input type='submit' value='edit' />
        </div>
      </form>
</div>""" % (filepath)

