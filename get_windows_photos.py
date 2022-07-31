import shutil
import filecmp
import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
import yaml
from yaml import CLoader as Loader

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=Loader)

# minimum number of kilobytes a file must be before it is picked up by the scraper
MIN_KB = 200

def get_images():
  users = cfg['users']
  keep_vertical = cfg['keep_vertical']
  for user in users:
    horizontal_destination = cfg['destination_horizontal']
    if keep_vertical:
      vertical_destination = cfg['destination_vertical']
    file_destination = ''
    source = f"C:\\Users\\{user}\\AppData\\Local\\Packages\\Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy\\LocalState\\Assets"
    # get list of file sizes in destination folder
    dest_files_data = [[os.path.join(horizontal_destination, file), os.stat(os.path.join(horizontal_destination, file)).st_size] for file in os.listdir(horizontal_destination)]
    if keep_vertical:
      dest_files_data += [[os.path.join(vertical_destination, file), os.stat(os.path.join(vertical_destination, file)).st_size] for file in os.listdir(vertical_destination)]
    dest_files = [os.path.join(horizontal_destination, f) for f in os.listdir(horizontal_destination)] + [os.path.join(vertical_destination, f) for f in os.listdir(vertical_destination)]
    # copy image files
    for file in os.listdir(source):
      file_location = os.path.join(source, file)
      # filter for only images of a certain size or higher to avoid pulling in logos
      if os.stat(file_location).st_size >= MIN_KB * 1000:
        is_duplicate = False
        for dest_file in dest_files:
          # if files are equal, they are duplicates
          if filecmp.cmp(file_location, dest_file):
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
        if cfg['rename_images']:
          name = get_image_name(file_location) + '.jpg'
        else:
          name = file + '.jpg'
        try:
          shutil.copy(file_location, os.path.join(file_destination, name))
        except FileExistsError:
          print(f'existing image {name} found in {orientation} destination folder')
          continue
        print(f'New image {name} added to {orientation} destination folder')
  print(f'All images named and copied for user {user}')
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
  try:
    print('Searching for image title...')
    searchUrl = 'http://www.google.com/searchbyimage/upload'
    multipart = {'encoded_image': (filePath, open(filePath, 'rb')), 'image_content': ''}
    response = requests.post(searchUrl, files=multipart, allow_redirects=False)
    print('Parsing response...')
    fetchUrl = response.headers['Location']
    soup = BeautifulSoup(requests.get(fetchUrl, headers=HEADERS).text, features='html.parser')
    print('Response parsed! Naming file...')
    return soup.find('input', {'aria-label':"Search"}).get('value').title()
  except Exception as e:
    print("error retrieving image name")
    raise(e)

def getDimension(filename):
  im = Image.open(filename)
  return im.size

if __name__ == "__main__":
  get_images()
