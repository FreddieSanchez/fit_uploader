#!/usr/bin/python
''' 
Freddie Sanchez - 2013-04-27

This script uses the Selenium webdriver to automate .fit file uploads to various sites.

Currently, runningahead.com is only supported. I'm going to change this to allow for
multiple sites via classes. It also uses a virtual frame buffer to allow for a headless
expierence.
'''
import sys, argparse, getpass
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver 
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from pyvirtualdisplay import Display


class RunningSite:
  def __init__(self):
    self.login = None;

  def login(self,driver,user,passwd):
    raise NotImplementedError("Subclass must implement abstract method")

class Endomondo(RunningSite):
  def __init__(self):
    self.login_addr = "https://www.endomondo.com/access"
  
  def login(self,driver,user,passwd):
    driver.get(self.login_addr) 
    email_field = driver.find_element_by_name('email')
    email_field.send_keys(user)
    passwd_field = driver.find_element_by_name('password')
    passwd_field.send_keys(passwd)
    driver.find_element_by_class_name('signInButton').click()
    return "home" in driver.current_url


  def upload_file(self,driver,file):
    driver.get("http://www.endomondo.com/workouts/create")
    driver.find_element_by_class_name('fileImport').click()

    # Wait for the "Upload" Button to be active, then click it.
    element = WebDriverWait(driver, 10).until(
            lambda driver : driver.find_element_by_class_name("iframed"))

    driver.switch_to_frame(element)
    # select the FIT

    file_field = driver.find_element_by_name("uploadFile")
    file_field.send_keys(file)
    
    driver.find_element_by_name("uploadSumbit").click()
    element = WebDriverWait(driver,10).until(
        lambda driver: driver.find_element_by_name("reviewSumbit"))
    element.click()

    return True

  def fill_in_details(self,driver,notes):
    pass

class RunningAhead(RunningSite):
  def __init__(self):
    self.login_addr = "https://www.runningahead.com/login"
  
  def login(self,driver,user,passwd):
    driver.get(self.login_addr) 
    email_field = driver.find_element_by_id('ctl00_ctl00_ctl00_SiteContent_PageContent_MainContent_email')
    email_field.send_keys(user)
    passwd_field = driver.find_element_by_id('ctl00_ctl00_ctl00_SiteContent_PageContent_MainContent_password')
    passwd_field.send_keys(passwd)
    driver.find_element_by_name('ctl00$ctl00$ctl00$SiteContent$PageContent$MainContent$login').submit()
    if "Summary" not in driver.title:
      return False
    return True

  def upload_file(self,driver,file):
    driver.get("http://www.runningahead.com/logs/4c335315d378452b822a9543fc62789d/tools/import")
    drop_down = Select(driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$m_type"))
    # select the FIT
    drop_down.select_by_index(6)
    file_field = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$m_file")
    file_field.send_keys(file)

    # Wait for the "Upload" Button to be active, then click it.
    element = WebDriverWait(driver, 10).until(
            lambda driver : driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$m_import"))
    element.click()
    return True

  def fill_in_details(self,driver,notes):
    WebDriverWait(driver,2)
    driver.back()
    edit_link = driver.find_elements_by_class_name("Button")[0]
    edit_link.click()

    # Grab all the resources
    weight_box = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Weight")
    temperature_box = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Temperature")
    notes_box = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Notescta")
    save_button = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Save")
    stars = driver.find_elements_by_class_name("Empty")

    weight = raw_input("Weight:")
    weight_box.send_keys(weight)
    # TODO - get temperature from another source
    temperature = raw_input("Temperature:")
    temperature_box.send_keys(temperature)
    notes_box.send_keys(notes)
    quality = raw_input("Quality:1-10:")
    stars[int(quality)].click()
    effort = raw_input("Effort:1-10:")
    stars[int(effort)+10].click()
    save_button.click()
    
def parse_args():
  parser = argparse.ArgumentParser(description="Uploads a FIT file to one running/training site.")
  parser.add_argument("--input_file","-i",help="Fit file to upload",required=True)
  parser.add_argument("--user","-u",help="username for the site",required=True)
  parser.add_argument("--site","-s",help="site to upload",choices = RUNNING_SITES.keys(),required=True)
  parser.add_argument("--visible","-v",help="debug level",default=False)
  parser.add_argument("--notes_file","-n",help="notes file")
  args = parser.parse_args()
  return args

def main():
  # parse the arguments
  args = parse_args()
  # check the arguments 
  check_args(args)

  running_site = site(args)

   # Get the site password
  passwd = getpass.getpass()

  # start the virtual display
  display = Display(visible = args.visible, size=(800,600))
  display.start()

  # start selenium web driver.
  driver = webdriver.Firefox()

  # Attempt to login to the site
  if not running_site.login(driver,args.user,passwd):
    exit(driver,display,"Could not login! Please check your username and password.")
  print "Successfully logged in!"
  
  # attempt to upload the file.
  if not running_site.upload_file(driver,args.input_file):
    exit(driver,display,"Could not upload file, sorry!")
  print "Successfully uploaded file!"

  notes = ""
  if not args.notes_file:
    notes = raw_input("Notes:")
  else:
    file = open(args.notes_file)
    notes = file.read()
    file.close()

  # fill in the details for the run
  running_site.fill_in_details(driver,notes)
  
  driver.close()
  display.stop()

''' 
This function checks the arguments for any errors.

1) If notes file specified, if it exists
'''
def check_args(args):
  if args.notes_file:
    try:
      open(args.notes_file)
    except IOError as e:
      print "File",args.notes_file,"not found!"
      sys.exit(1)

def site(args):
  return RUNNING_SITES[args.site]

def usage(error=""):
  print error
  print 'test.py -i [--input_file=] <inputfile> -s [--site=] <ra|endomondo>'

def exit(driver,display,err_msg):
  print err_msg
  driver.close()
  display.stop()
  sys.exit(-1)


def login(driver,display,args):
  passwd = getpass.getpass()
  driver = webdriver.Firefox()
  if not rs.login(driver,args.user,passwd):
    exit(driver,display,"Could not login! Please check your username and password.")
  print "Successfully logged in!"
  return driver

def upload_file(driver, display,args):
  if not rs.upload_file(driver):
    exit(driver,display,"Could not upload file, sorry!")
  print "Successfully uploaded file!"
  return driver

def fill_in_details(driver,display,args):
  if args.site == "runningahead":
    WebDriverWait(driver,2)
    driver.back()
    edit_link = driver.find_elements_by_class_name("Button")[0]
    edit_link.click()
    # Grab all the resources
    weight_box = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Weight")
    temperature_box = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Temperature")
    notes_box = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Notescta")
    save_button = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Save")
    stars = driver.find_elements_by_class_name("Empty")

    notes = ""
    if not args.notes_file:
      notes = raw_input("Notes:")
    else:
      file = open(args.notes_file)
      notes = file.read()
      file.close()
 
    weight = raw_input("Weight:")
    weight_box.send_keys(weight)
    # TODO - get temperature from another source
    temperature = raw_input("Temperature:")
    temperature_box.send_keys(temperature)
    notes_box.send_keys(notes)
    quality = raw_input("Quality:1-10:")
    stars[int(quality)].click()
    effort = raw_input("Effort:1-10:")
    stars[int(effort)+10].click()
    save_button.click()

RUNNING_SITES = { "runningahead": RunningAhead(),
                  "endomondo": Endomondo(),
                  "dailymile":None
                }
if __name__ == "__main__":
  main()
