import shutil
import os
import requests
from bs4 import BeautifulSoup
import tempfile
import yaml
from yaml import CLoader as Loader

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=Loader)

min_kb = 200

def get_images():
  users = cfg['users']
  for user in users:
    destination = cfg['destination']
    source = "C:\\Users\\" + user + "\\AppData\\Local\\Packages\\Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy\\LocalState\\Assets"
    cur_dest_files = os.listdir(destination)
    # copy image files
    with tempfile.TemporaryDirectory() as temp_dir:
      # first, copy all files from the desktop to a temporary folder for processing and sorting
      for file in os.listdir(source):
        source_location = source+"\\"+file
        if os.stat(source_location).st_size >= min_kb * 1000:
          shutil.copy(source_location, temp_dir)
          os.rename(temp_dir+"\\"+file, temp_dir+"\\"+file+".jpg")
      # rename all temporary files to their proper names
      for file in os.listdir(temp_dir):
        file_location = temp_dir+"\\"+file
        img_size = getDimension(file_location)
        orientation = ''
        if (img_size[0] == 1920):
          orientation = 'horizontal'
        else:
          orientation = 'vertical'
        name = get_image_name(file_location).replace(' ', '_')+ "_" + orientation +'.jpg'
        os.rename(file_location, temp_dir+"\\"+name)
        # if the renamed file does not already exist in our permanent folder, copy it there
        if name not in cur_dest_files:
            shutil.copy(temp_dir + "\\" + name, destination)
    print('All images named and copied for user {}'.format(user))
  print('opening destination folder!')
  os.startfile(os.path.realpath(destination))

HEADERS = {
            'Accept': ('text/html,application/xhtml+xml,application/'
                       'xml;q=0.9,*/*;q=0.8'),
            'Accept-Encoding': 'gzip;deflate;br',
            'Accept-Language': 'en-US,en;q=0.5',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64'
                           '; rv:67.0) Gecko/20100101 Firefox/67.0')
            }

def get_image_name(filePath):
  searchUrl = 'http://www.google.com/searchbyimage/upload'
  multipart = {'encoded_image': (filePath, open(filePath, 'rb')), 'image_content': ''}
  response = requests.post(searchUrl, files=multipart, allow_redirects=False)
  fetchUrl = response.headers['Location']
  soup = BeautifulSoup(requests.get(fetchUrl, headers=HEADERS).text, features='html.parser')
  return soup.find('input', title="Search").get('value').title()

def getDimension(filename):
   # open image for reading in binary mode
   with open(filename,'rb') as img_file:
    # height of image (in 2 bytes) is at 164th position
    img_file.seek(163)

    # read the 2 bytes
    a = img_file.read(2)

    # calculate height
    height = (a[0] << 8) + a[1]

    # next 2 bytes is width
    a = img_file.read(2)

    # calculate width
    width = (a[0] << 8) + a[1]

    return [width, height]

if __name__ == "__main__":
  get_images()
