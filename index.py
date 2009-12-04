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
					<div id='images'></div>
				</div>
			
				<div id="tagblock">
					<img id='add-tag' src="/images/plus.png"></img>
					<div id='tags'></div>
				</div>	
		
				<div id='misc'>
					<div id="phototitle">
						<input name='phototitle' type='text' size='50'/> Phototitle
					</div>
					<div id="photodescription">
						<input name='photodescription' type='text' size='50'/> Photodescription
					</div>
					<div id="photoset">
						<input name='photoset' type='text' size='50'/> Photoset
					</div>
					<div id="filepath">
						<input name='filepath' type='text' value='%s%s/' size='50' /> Filepath
					</div>
				</div>
				
				<div id='logtext'>
					<input name='title' size='60' /></textarea> <br /> <br />
					<textarea name='logtext' id='mceEditor' wrap=hard rows='20' cols='100'></textarea>
				</div>
				<div id='submit'>
					<input name='upload' type='checkbox' checked/> Upload to server? <br /> <br />
					<input type='submit' value='Write XML' />
				</div>
			</div>
		</form>
	</body>
</html>""" % (filepath,today)

