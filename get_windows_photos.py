import shutil
import filecmp
import os
import requests
from bs4 import BeautifulSoup
import tempfile
import yaml
from yaml import CLoader as Loader

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=Loader)

min_kb = 200

rename_images = cfg['rename_images']

def get_images():
  users = cfg['users']
  keep_vertical = cfg['keep_vertical']
  for user in users:
    horizontal_destination = cfg['destination_horizontal']
    if keep_vertical:
      vertical_destination = cfg['destination_vertical']
    file_destination = ''
    source = "C:\\Users\\" + user + "\\AppData\\Local\\Packages\\Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy\\LocalState\\Assets"
    # get list of file sizes in destination folder
    dest_files_data = [[horizontal_destination + "\\" + file, os.stat(horizontal_destination + "\\" + file).st_size] for file in os.listdir(horizontal_destination)]
    if keep_vertical:
      dest_files_data += [[vertical_destination + "\\" + file, os.stat(vertical_destination + "\\" + file).st_size] for file in os.listdir(vertical_destination)]
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
        # if the renamed file does not already exist in our permanent folder, copy it there
        filesize = os.stat(file_location).st_size
        is_duplicate = False
        epsilon = .1
        for file_data in dest_files_data:
          # if file is same size as one in destination folder
          if file_data[1] == filesize or (file_data[1] >= filesize * (1-epsilon) and file_data[1] <= filesize * (1+epsilon)):
            # if files are equal, break
            if filecmp.cmp(file_location, file_data[0]):
              is_duplicate = True
              print('Duplicate found! Moving to next file...')
              break
        # if the file is a duplicate, skip it
        if is_duplicate:
          continue
        img_size = getDimension(file_location)
        orientation = ''
        if (img_size[0] == 1920):
          orientation = 'horizontal'
          file_destination = horizontal_destination
        elif keep_vertical:
          orientation = 'vertical'
          file_destination = vertical_destination
        identifier = ''
        if keep_vertical and orientation == 'vertical':
          identifier = '_vert-tag'
        if rename_images:
          name = get_image_name(file_location) + identifier + '.jpg'
        else:
          name = file + '.jpg'
        os.rename(file_location, temp_dir+"\\"+name)
        shutil.copy(temp_dir + "\\" + name, file_destination)
        print('New image added to ' + orientation + ' destination folder')
    print('All images named and copied for user {}'.format(user))
    # remove vertical identifier tag in the vertical destination folder
    for v_file in os.listdir(vertical_destination):
      if v_file[-13:] == "_vert-tag.jpg":
        try:
          os.rename(vertical_destination+"\\"+v_file, vertical_destination+ "\\" + v_file[0:-13] + ".jpg")
        except FileExistsError:
          os.remove(vertical_destination + "\\" + v_file)
  print('opening horizontal destination folder!')
  os.startfile(os.path.realpath(horizontal_destination))

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
  print('Searching for image title...')
  searchUrl = 'http://www.google.com/searchbyimage/upload'
  multipart = {'encoded_image': (filePath, open(filePath, 'rb')), 'image_content': ''}
  response = requests.post(searchUrl, files=multipart, allow_redirects=False)
  print('Parsing response...')
  fetchUrl = response.headers['Location']
  soup = BeautifulSoup(requests.get(fetchUrl, headers=HEADERS).text, features='html.parser')
  print('Response parsed! Naming file...')
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
