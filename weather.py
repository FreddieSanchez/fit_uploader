#!/usr/bin/python
'''
Freddie Sanchez - 2014-02-28

This script queries weather underground for the given location. If no location
is specified, a default will be used.
'''
import sys, requests
'''
This function takes a location (zip code, city, city+state, lat+long coordinates,etc
and returns back a sample of the relavent weather information.
'''
def current_weather(location="32.368197,-111.1396966"):
  url = "http://api.wunderground.com/api/bdf13372b1f7e319/conditions/q/"+location+".json"
  r = requests.get(url)
  j = r.json()
  if 'error' in j['response']:
    return {'weather_string':j['response']['error']['description']}
  return {'weather_string':j['current_observation']['weather']  + " " + \
                           j['current_observation']['temperature_string'] + " " +\
                           j['current_observation']['wind_string'],
          'temp_f':j['current_observation']['temp_f'],
          'temp_c':j['current_observation']['temp_c'],
          'humidity':j['current_observation']['relative_humidity'],
          'wind_speed':j['current_observation']['wind_mph'],
          'wind_gust_mph':j['current_observation']['wind_gust_mph']}
''' 
NOT Yet implemented!
'''
def forcast(location="32.368197,-111.1396966"):
  url = "http://api.wunderground.com/api/bdf13372b1f7e319/forecast/q/"+location+".json"
  r = requests.get(url)
  j = r.json()
  if 'error' in j['response']:
    return {'weather_string':j['response']['error']['description']}
  return {'weather_string':j['current_observation']['weather']  + " " + \
                           j['current_observation']['temperature_string'] + " " +\
                           j['current_observation']['wind_string'],
          'temp_f':j['current_observation']['temp_f'],
          'temp_c':j['current_observation']['temp_c'],
          'humidity':j['current_observation']['relative_humidity'],
          'wind_speed':j['current_observation']['wind_mph'],
          'wind_gust_mph':j['current_observation']['wind_gust_mph']}

def main():
  ''' if the only argument was the file name, call to get the current weather from the
      default location
  '''
  if len(sys.argv) == 1:
    print current_weather()['weather_string']
  else:
    ''' get the weather for each location specified and print the result'''
    for location in sys.argv[1:]:
      print current_weather(location)['weather_string']

if __name__ == "__main__":
  main()

