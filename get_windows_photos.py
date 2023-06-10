import shutil
import filecmp
import os
from PIL import Image
import yaml
from yaml import CLoader as Loader
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tempfile
import re

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile, Loader=Loader)

# minimum number of kilobytes a file must be before it is picked up by the scraper
MIN_KB = 200

OPTIONS = Options()
OPTIONS.add_argument('--headless=new')


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
          try:
            name_suggestion = get_image_name(file_location)
            name = "".join([c for c in name_suggestion if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            name = re.sub(' +', ' ', name)
            name += ".jpg"
          except Exception as e:
            print('There was an error generating a name suggestion for this image.')
            print(e)
            name = file + '.jpg'
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


def get_image_name(filePath):
  DRIVER = webdriver.Chrome(os.path.abspath(cfg['chromedriver_abs_path']), options=OPTIONS)
  # Open the website
  DRIVER.get('https://images.google.com/')

  # if it shows up, dismiss the sign in to google popup
  try:
    WebDriverWait(DRIVER, 10).until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR,"iframe")))
    WebDriverWait(DRIVER, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label=\"No thanks\"]'))).click()
    DRIVER.switch_to.default_content()
    time.sleep(.1)
  except Exception:
    pass

  # Find cam button
  WebDriverWait(DRIVER, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@aria-label=\"Search by image\" and @role=\"button\"]"))).click()

  # Find image input
  WebDriverWait(DRIVER, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@name=\"encoded_image\"]")))
  upload_btn = DRIVER.find_element("name", 'encoded_image')
  # make local file something google can read
  tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.jpg')
  tmp.close()
  shutil.copyfile(filePath, tmp.name)
  # send it to google (automatically submits when a file is submitted)
  upload_btn.send_keys(tmp.name)

  WebDriverWait(DRIVER, 10).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'h2'), 'Visual matches'))
  try:
    link = DRIVER.find_element(By.CSS_SELECTOR, "c-wiz div[data-is-touch-wrapper=\"true\"] a")
    print('Lens identified this as a place of interest, using that identification')
    name = link.get_attribute('aria-label').replace("Search ", "")
  except Exception as e:
    print('Lens did not have a helpful quick link, using first search option')
    first_link = DRIVER.find_element('xpath', '//div[@data-card-token=\"0-0\"]')
    name = first_link.get_attribute('data-item-title')
  DRIVER.quit()
  return name

def getDimension(filename):
  im = Image.open(filename)
  return im.size

if __name__ == "__main__":
  get_images()