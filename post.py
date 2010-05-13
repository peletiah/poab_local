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
from time import strftime
import hashlib
import mod_exif #custom
import glob
import tktogpx2 #custom

form = cgi.FieldStorage()
title = form.getvalue('title','')
logtext = form.getvalue('logtext','')
phototitle = form.getvalue('phototitle','')
photoset = form.getvalue('photoset','')
filepath = form.getvalue('filepath','')
basepath=filepath.rsplit('/',2)[0]+'/'
datepath=filepath.rsplit('/',2)[1]
trackpath=basepath+datepath+"/trackfile/"
createdate=form.getvalue('createdate','')
motor = form.getvalue('motor','')
upload = form.getvalue('upload','')
modimg = form.getvalue('modimg','')


####### Create a proper imagelist #########
imgdict={}
imagepath=filepath+'images/'
imagelist=list()
for imgname in os.listdir(imagepath+'best'):
    filetypes=('.png','.jpg','.jpeg','.gif','.tif')
    if imgname.lower().endswith(filetypes):
        desc=''
        number=''
        logphoto=False
        if modimg=='on':
            #mod_exif.copy_exif(imagepath+'raw',imagepath+'best',imgname)
            #mod_exif.remove_orientation(imagepath+'best',imgname)
            mod_exif.resize_990(imagepath+'best',imagepath+'best_990',imgname)
        try:
            image_full=open(imagepath+'best/'+imgname).read()
        except IOError:
            pass
        hash_full=hashlib.sha256(image_full).hexdigest()
        try:
            image_resized=open(imagepath+'best_990/'+imgname).read()
            hash_resized=hashlib.sha256(image_resized).hexdigest()
        except IOError:
            pass   
        i=1
        num_of_img=len(glob.glob(imagepath+'best/*.jpg'))
        while i <= num_of_img:
            try:
                if imgname == form.getvalue('img'+str(i),''):
                    number='img'+str(i)
                    try:
                        desc=form.getvalue('description'+str(i),'')
                    except NameError:
                        desc=''
                    logphoto=True
                else:
                    fromform=form.getvalue('img'+str(i),'')
            except NameError:
                logphoto=False
            i=i+1
        class imgproperty:
            number=number
            name=imgname
            hash_full=hash_full
            hash_resized=hash_resized
            description=desc
            logphoto=logphoto
        imagelist.append(imgproperty)

####### Create a proper taglist #########
i=1
taglist=list()
while i < 100:
	try:
		temptag=form.getvalue('tag'+str(i),'')
		#temptag=tag1
		if temptag:
			taglist.append(temptag)
		i=i+1
	except NameError:
		i=i+1

####### Color of the track is set by transport-type #######

if motor=='on':
    trk_color='666666'
else:
    trk_color='FF0000'

if modimg=='on':
    for trackfile in os.listdir(trackpath):
        if trackfile.lower().endswith('.tk1'):
            #passes outputDir,gpx-filename and tkFileName to tk2togpx.interactive to convert the tk1 to gpx
            if os.path.exists(trackpath+trackfile[:-3]+'gpx'): # is there already a gpx-file with this name?
                pass
            else:
                tktogpx2.interactive(trackpath,trackfile.split('.')[0]+'.gpx',trackpath+trackfile)
        else:
            pass
    os.system("/usr/bin/perl /var/www/gpsPhoto.pl --dir "+imagepath+"best/ --delete-geotag > /var/log/poab/geotag.log 2>&1")
    os.system("/usr/bin/perl /var/www/gpsPhoto.pl --dir "+imagepath+"best/ --gpsdir "+trackpath+" --timeoffset 0 --maxtimediff 1200 > /var/log/poab/geotag.log 2>&1")
    os.system("/usr/bin/perl /var/www/gpsPhoto.pl --dir "+imagepath+"best_990/ --delete-geotag > /var/log/poab/geotag.log 2>&1")
    os.system("/usr/bin/perl /var/www/gpsPhoto.pl --dir "+imagepath+"best_990/ --gpsdir "+trackpath+" --timeoffset 0 --maxtimediff 1200 > /var/log/poab/geotag.log 2>&1")


######### write to contentfile.xml #########
print "Content-type: text/html"
print 

xmlcontent='''<?xml version="1.0" encoding="UTF-8"?>
<content>
  <log>
    <topic><![CDATA['''+ str(title) +''']]></topic>
    <logtext><![CDATA['''+ str(logtext) + ''']]></logtext>
    <filepath><![CDATA['''+ filepath + ''']]></filepath>
    <phototitle><![CDATA['''+ phototitle + ''']]></phototitle>
    <photoset><![CDATA['''+ photoset + ''']]></photoset>
    <createdate><![CDATA['''+ createdate + ''']]></createdate>
    <trk_color><![CDATA['''+ trk_color + ''']]></trk_color>
    <num_of_img><![CDATA['''+ str(num_of_img) + ''']]></num_of_img>'''

for imgproperty in imagelist:
    xmlcontent=xmlcontent + '''    <img>
      <no>'''+ imgproperty.number +'''</no>
      <name>''' + imgproperty.name +'''</name>
      <hash_full>''' + imgproperty.hash_full +'''</hash_full>
      <hash_resized>'''+ imgproperty.hash_resized +'''</hash_resized>
      <description><![CDATA['''+ imgproperty.description +''']]></description>
      <logphoto>'''+ str(imgproperty.logphoto) +'''</logphoto>
    </img>\n'''

for tag in taglist:
    xmlcontent=xmlcontent + '''    <tag><![CDATA['''+ str(tag) + ''']]></tag>\n'''
xmlcontent=xmlcontent + '''</log>
</content>'''

xmlfile=open(basepath+datepath+'-contentfile.xml','w')
xmlfile.write(xmlcontent)
xmlfile.close()




############ Preview the xmlfile we just created ###############

tree = etree.parse(basepath+datepath+'-contentfile.xml')
root = tree.getroot()
logs=root.getiterator("log")
for log in logs:
    topic =  log.find('topic').text.replace("&gt;",">").replace("&lt;","<")
    logtext =  log.find('logtext').text.replace("&gt;",">").replace("&lt;","<")
    filepath =  log.find('filepath').text
    photosetname =  log.find('photoset').text
    phototitle =  log.find('phototitle').text
    createdate =  log.find('createdate').text
    num_of_img =  int(log.find('num_of_img').text)
viewdate = time.strptime(createdate,'%Y-%m-%d %H:%M:%S')
viewdate = strftime('%B %d, %Y',viewdate)
xmltaglist=list()

images = root.getiterator("img")
for image in images:
    if image.find('logphoto').text=='True':
        i=1
        while i <= num_of_img:
            if image.find('no').text=='img'+str(i):
                if image.find('description').text:
                    logtext=logtext.replace('[img%s]' % str(i),'<div id=\'log_inlineimage\'><img src="/preview/'+filepath.split('/')[4]+'/images/best/'+image.find('name').text+'" class="resize"><br>'+image.find('description').text+'</div>')
                else:
                    logtext=logtext.replace('[img%s]' % str(i),'<div id=\'log_inlineimage\'><img src="/preview/'+filepath.split('/')[4]+'/images/best/'+image.find('name').text+'" class="resize"></div>')
            i=i+1

query_xmltaglist='//tag'
for element in tree.xpath(query_xmltaglist):
    xmltaglist.append(element.text)

#for image in xmlimglist:
#    if xmlimgdesc[image]:
#        logtext=logtext.replace('[img'+str(i)+']','<div id=\'log_inlineimage\'><img src="/preview/'+filepath.split('/')[4]+"/images/best/"+image+'" class="resize"><br>'+xmlimgdesc[image]+'</div>')
#    else:
#        logtext=logtext.replace('[img'+str(i)+']','<div id=\'log_inlineimage\'><img src="/preview/'+filepath.split('/')[4]+"/images/best/"+image+'" class="resize"></div>')
#    i=i+1


try:
    #logtext_u=logtext.replace(u'\xa0',u'')
    logtext_u = unicode(logtext, "ascii")
except UnicodeError:
    #logtext_u=logtext.replace(u'\xa0',u'')
    print 'except UnicodeError'
    logtext_u = unicode(logtext, "utf-8")
except TypeError:
    #logtext_u=logtext.replace(u'\xa0',u'')
    print 'except TypeError'
    logtext_u = logtext
except:
    print 'except'
    # value was valid ASCII data

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
                        <td class="leftcol">""" + viewdate + """</td>
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
                """ + logtext_u.replace(u'\xa0',u'').replace(u'\xbb',u'').replace(u'\xab',u'') + """
                </div>
            </div>
    </div>
<form action='edit.py'>
        <div id="edit">
            <input name='filepath' type='text' value='%s' size='50' />
            <input type='submit' value='edit' />
        </div>
      </form>
<form action='upload.py'>
        <div id="upload">
            <input name='smallsize' type='checkbox' checked/>Upload 990px<br />
            <input name='fullsize' type='checkbox' unchecked/>Upload Fullsize<br />
            <input name='filepath' type='text' value='%s' size='50' />
            <input type='submit' value='upload' />
        </div>
      </form>
</div>""" % (filepath,filepath)

