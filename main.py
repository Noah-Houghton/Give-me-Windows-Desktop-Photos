import shutil
import os


default_user="Stodg"
default_destination = "C:\\Users\\"+ default_user +"\\Dropbox\\Windows Desktop Images"

min_kb = 200

def get_images(user=default_user, destination=default_destination):
  source = "C:\\Users\\" + user + "\\AppData\\Local\\Packages\\Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy\\LocalState\\Assets"
  cur_dest_files = os.listdir(destination)
  # copy image files
  for file in os.listdir(source):
    file_location = source+"\\"+file
    # if the file is greater than our max size AND does not already exist in target folder, copy it
    if os.stat(file_location).st_size >= min_kb * 1000 and file+".jpg" not in cur_dest_files:
        shutil.copy(file_location, destination)
  # rename files to add .jpg to the end if necessary
  dest_files = os.listdir(destination)
  for file in dest_files:
    file_location = destination+"\\"+file
    if not file.endswith('.jpg') and os.path.isfile(file_location):
      os.rename(file_location, file_location+'.jpg')


if __name__ == "__main__":
  get_images()
