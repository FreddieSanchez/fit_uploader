#!/usr/bin/python
''' 
Freddie Sanchez - 2013-04-27

This script uses the Selenium webdriver to automate .fit file uploads to various sites.

Currently, runningahead.com is only supported. I'm going to change this to allow for
multiple sites via classes. It also uses a virtual frame buffer to allow for a headless
expierence.
'''
import sys, argparse, getpass, requests
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver 
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from pyvirtualdisplay import Display
from fitparse import FitFile

class RunningSite:
  def __init__(self):
    self.login = None;

  def login(self,driver,user,passwd):
    raise NotImplementedError("Subclass must implement abstract method")
  def upload_file(self,driver,file):
    raise NotImplementedError("Subclass must implement abstract method")
  def fill_in_details(self,driver,notes,fit_file):
    raise NotImplementedError("Subclass must implement abstract method")

  def get_weather(self,fit_file):
    '''

  '''
    f = FitFile(fit_file)
    f.parse()
    records = list(f.get_messages(name='record'))
    lat = records[0].get_value('position_lat')
    long = records[0].get_value('position_long')
    lat  = str(lat * (180.0 / 2**31))
    long = str(long * (180.0 / 2**31))
    #Grab all the resources
    url = "http://api.wunderground.com/api/bdf13372b1f7e319/conditions/q/"+lat+","+long+".json"
    r = requests.get(url)
    j = r.json()
    return {'weather_string':j['current_observation']['weather']  + " " + \
                             j['current_observation']['temperature_string'] + " " +\
                             j['current_observation']['wind_string'],
            'temp_f':j['current_observation']['temp_f'],
            'temp_c':j['current_observation']['temp_c'],
            'humidity':j['current_observation']['relative_humidity'],
            'wind_speed':j['current_observation']['wind_mph'],
            'wind_gust_mph':j['current_observation']['wind_gust_mph']}



class DailyMile(RunningSite):
  def __init__(self):
    self.login_addr = "http://www.dailymile.com/login"
    self.distance = 0
    self.time = []

  
  def login(self,driver,user,passwd):
    driver.get(self.login_addr) 
    email_field = driver.find_element_by_id('user_email')
    email_field.send_keys(user)
    passwd_field = driver.find_element_by_id('user_password')
    passwd_field.send_keys(passwd)
    driver.find_element_by_xpath('//*[@id="login_button"]/dd/input').click()
    return "login" not in driver.current_url

  def upload_file(self,driver,file):
    f = FitFile(file)
    f.parse()
    records = list(f.get_messages(name='record'))
    self.distance = records[-1].get_value('distance') / 1609.347219 
    self.time = str(records[-1].get_value('timestamp') - records[0].get_value('timestamp')).split(":")
    return True

  def fill_in_details(self,driver,notes,fit_file):
    title_field = driver.find_element_by_id('entry_title')
    distance_field = driver.find_element_by_id("entry_distance")
    hours_field = driver.find_element_by_id("hours_of_time")
    minutes_field = driver.find_element_by_id("minutes_of_time")
    seconds_field = driver.find_element_by_id("seconds_of_time")
    notes_field = driver.find_element_by_id("entry_content_text")
    
    # Use the first line of the Notes file for the title.
    title_field.send_keys(notes.split("\n")[0])
    distance_field.send_keys(str(self.distance))
    hours_field.send_keys(str(self.time[0]))
    minutes_field.send_keys(str(self.time[1]))
    seconds_field.send_keys(str(self.time[2]))
    notes_field.send_keys(notes)

    driver.find_element_by_xpath('//*[@id="entry_workout_form"]/div[4]/div[3]/div[3]/ul/li[1]/input').click()


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

  def fill_in_details(self,driver,notes,fit_file):

    element =  WebDriverWait(driver, 10).until(
            lambda driver : driver.find_element_by_partial_link_text('EDIT'))
    element.click()

    element =  WebDriverWait(driver, 10).until(
            lambda driver : driver.find_element_by_id('workoutName'))
    element.send_keys(notes.split("\n")[0])

    element = driver.find_element_by_id("workoutEditNotes")
    element.send_keys(notes)
    
    driver.find_element_by_name('saveButton').click()
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

  def fill_in_details(self,driver,notes,fit_file):
    WebDriverWait(driver,5)
    driver.back()
    edit_link = driver.find_elements_by_class_name("Button")[0]
    edit_link.click()

    ## Wait for the "Upload" Button to be active, then click it.
    weight_box = WebDriverWait(driver, 10).until(
            lambda driver : driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Weight"))
    temperature_box = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Temperature")
    notes_box = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Notescta")
    save_button = driver.find_element_by_name("ctl00$ctl00$ctl00$SiteContent$PageContent$TrainingLogContent$Save")
    stars = driver.find_elements_by_class_name("Empty")

    weight = raw_input("Weight:")
    weight_box.send_keys(weight)
    
    weather = self.get_weather(fit_file)
    temperature = str(int(weather['temp_f']))
    temperature_box.send_keys(temperature)
    weather_summary = weather['weather_string']


    notes_box.send_keys( weather_summary + "\n")
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
  display = Display(visible = args.visible, size=(1600,900))
  display.start()

  # start selenium web driver.
  driver = webdriver.Firefox()

  # Attempt to login to the site
  if not running_site.login(driver,args.user,passwd):
    exit(driver,display,"Could not login! Please check your username and password.")
  print "Successfully logged in!"
  
  running_site.get_weather(args.input_file)
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
  running_site.fill_in_details(driver,notes,args.input_file)
  
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

RUNNING_SITES = { "runningahead": RunningAhead(),
                  "endomondo": Endomondo(),
                  "dailymile": DailyMile()
                }
if __name__ == "__main__":
  main()
