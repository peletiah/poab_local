import mod_exif
import os

#mod_exif.copy_exif(imagepath+'raw',imagepath+'best',imgname)
#mod_exif.remove_orientation(imagepath+'best',imgname)
#mod_exif.resize_990(imagepath+'best',imagepath+'best_990',imagename)

jpgpath='/home/media/images/stmk_nov_09_sorted_2'
nefpath='/home/media/images/stmk_november_09'
for imagename in os.listdir(jpgpath):
    mod_exif.copy_exif(nefpath,jpgpath,imagename)
    mod_exif.remove_orientation(jpgpath,imagename)
#    mod_exif.resize_990(jpgpath,990path,imagename)
