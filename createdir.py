#!/usr/bin/python2.5

import os
from time import strftime


def createdir(today,filepath):
	if os.access(filepath+today+'/images_sorted',os.F_OK):
		pass
	else:
		os.makedirs(filepath+today+'/images_sorted')
	if os.access(filepath+today+'/images',os.F_OK):
		pass
	else:
		os.mkdir(filepath+today+'/images')
	if os.access(filepath+today+'/trackfile',os.F_OK):
		pass
	else:
		os.mkdir(filepath+today+'/trackfile')



if __name__ == "__main__":
	today=strftime("%Y-%m-%d")
	filepath='/srv/trackdata/bydate/'+str(today)
	createdir(today,filepath)

