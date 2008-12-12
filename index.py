#!/usr/bin/python
import cgi
from time import strftime

filepath='/srv/trackdata/bydate/'
today=strftime("%Y-%m-%d")

import createdir

createdir.createdir(today,filepath)

print "Content-type: text/html"
print
print """
<html>
<head>
<style type="text/css" media="screen">
      #images {
      }
    </style>
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
  <img id='add-element' src="/images/plus.png"></img>
    <div id='images'></div>
    <div id='misc'>
	<br />
	<input name='trackfile' type='file' value='trackfile' /> Trackfile
    </div>
    <div id="photoset">
        <input name='photoset' type='text' size='50'/> Photoset
    </div>
    <div id="filepath">
	<input name='filepath' type='text' value='%s%s/' size='50' /> Filepath
    </div>
    <br />
    <div id='title'>
      <input name='title' size='60' /></textarea>
    </div>
    <div id='logtext'>
      <textarea name='logtext' id='mceEditor' wrap=hard rows='20' cols='100'></textarea>
    </div>
    <div id='upload'>
	<input name='upload' type='checkbox' checked/> Upload to server?
    </div>
    <input type='submit' value='Write XML' />
</div>
</form>
</body>
</html>""" % (filepath,today)

