import requests
import re
from decouple import config

# expires on Dec 31
map_auth_token=config('Apple_Token')
token=requests.get('https://maps-api.apple.com/v1/token',headers={'Authorization':'Bearer {}'.format(map_auth_token)})
token=token.json()['accessToken']

error_count=0
def pre_process(location):
    location=re.sub("\s\s+"," ",location)  # Replace more than 1 spaces
    street=location.split('-')[0]
    street=street.strip()
    if "On Campus" in location:
        street="USC "+street
    else:
        street+=", Los Angeles, California"
    return street

def get_location(location):
    print(location)
    response = requests.get("https://maps-api.apple.com/v1/search",
                            params={'q': location, 'searchLocation': "34.02238903485463,-118.28511717567595",
                                    'userLocation': "34.02238903485463,-118.28511717567595", 'limitToCountries': "US"},
                            headers={'Authorization': 'Bearer {}'.format(token)})
    response = response.json()
    try:
        return response['results'][0]['coordinate']
    except:
        global error_count
        error_count+=1
        print(response,location)
    print(response)

import json
def test():
    file=open("locations_test.json",'r')
    locations=json.load(file)
    for loc in locations:
        print(get_location(pre_process(loc)))

test()
print(error_count)