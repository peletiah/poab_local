import cgi
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

form = cgi.FieldStorage()
filepath = form.getvalue('filepath','')
#basepath=filepath.rsplit('/',2)[0]+'/'
#datepath=filepath.rsplit('/',2)[1]



tree = etree.parse(filepath+'-contentfile.xml')
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

query_xmltaglist='//tag'
for element in tree.xpath(query_xmltaglist):
    xmltaglist.append(element.text)

imgstring=''
images = root.getiterator("img")
for image in images:
    if image.find('logphoto').text=='True':
        i=1
        while i <= num_of_img:
            if image.find('no').text=='img'+str(i):
                description=image.find('description').text.replace(">","&gt;").replace("<","&lt;").replace("\"",'&#34;')
                imgstring=imgstring+"""&#160;&#160;&#160;&#160;<input name="img%s" type="text" value="%s" /> IMG%s <br />
                &#160;&#160;&#160;&#160;<input name="description%s" type="text" value="%s"/> <br />""" % (i,image.find('name').text,i,i,description)
            i=i+1

i=1
tagstring=''
for tag in xmltaglist:
    tagstring=tagstring+"""<input name="tag%s" type="text" value="%s"/> tag%s <br />""" % (i,tag,i)
    i=i+1



print """
<html>
   <head>
      <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <link rel="stylesheet" type="text/css" href="/css/main.css" media="screen">
      <title>Yo yo yo!</title>
      <script type="text/javascript" src="/js/punymce/puny_mce.js"></script>
      <script type="text/javascript" src="/js/punymce/plugins/link/link.js"></script>
      <script type="text/javascript" src="/js/punymce/plugins/editsource/editsource.js"></script>
      <script type="text/javascript" src="/js/addremove.js"></script>
   </head>
   <body>


      <script type="text/javascript">
         var editor2 = new punymce.Editor({  
            id : 'mceEditor',
            plugins : 'Link,EditSource',
            toolbar : 'bold,italic,link,editsource',
            max_width : 500
         }); 
      </script>
      <form action='post.py'>
         <div id='log'>
            <div id='imageblock'>
               <img id='add-img' src="/images/plus.png"></img>
               <div id='images'>%s
               </div>
            </div>
         
            <div id="tagblock">
               <img id='add-tag' src="/images/plus.png"></img>
               <div id='tags'>%s</div>
            </div>   
      
            <div id='misc'>
<div id="phototitle">
                  <input name='phototitle' type='text' size='50' value='%s'/> Phototitle
               </div>
               <div id="photoset">
                  <input name='photoset' type='text' size='50' value='%s'/> Photoset
               </div>
               <div id="createdate">
                  <input name='createdate' type='text' size='50' value='%s'/>Createdate</div>
               <div id="filepath">
                  <input name='filepath' type='text' value='%s' size='50' /> Filepath
               </div>
            </div>
            
            <div id='logtext'>
               <input name='title' size='60' value='%s' /></textarea> <br /> <br />
               <textarea name='logtext' id='mceEditor' wrap=hard rows='20' cols='100'>%s</textarea>
            </div>
            <div id='submit'>
               <input name='modimg' type='checkbox' unchecked/>Modify images<br /> <br />
               <input type='submit' value='Write XML' />
            </div>
         </div>
      </form>
   </body>
</html>""" % (imgstring,tagstring,phototitle,photosetname,createdate,filepath,topic,logtext)
