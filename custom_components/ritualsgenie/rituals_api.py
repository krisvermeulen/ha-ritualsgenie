
import requests
import json
from urllib.parse import urlencode

name = "rituals-api"

class RitualsAPI:

    BASE_URL = 'https://rituals.sense-company.com'

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.userData = None
        self.hubs = {}
        self._login()

    def _login(self):
        url = '{}/ocapi/login'.format(self.BASE_URL)
        data = {'email': self.email, 'password': self.password}
        headers = {'Content-Type': 'application/json'}

        r = requests.post(url, json=data, headers=headers)

        if r.status_code == 200:
            self.userData = r.json()
            self._getHubs()
        else:
            print('Something went wrong with logging in: {}'.format(r.text()))

    def _getHubs(self):
        url = '{}/api/account/hubs/{}'.format(self.BASE_URL, self.userData['account_hash'])

        r = requests.get(url)

        if r.status_code == 200:
            for hub in r.json():
                hubName = str(hub['hub']['attributes']['roomnamec']).replace(' ','_').lower()
                self.hubs[hubName] = hub['hub']
        else:
            print('Something went wrong with retrieving hub info: {}'.format(r.text()))

    def availableHubs(self):
        return self.hubs.keys()

    def turnOn(self, hubId):
        return self._setAttributes(self.hubs[hubId], {'fanc': "1"})

    def turnOff(self, hubId):
        return self._setAttributes(self.hubs[hubId], {'fanc': "0"})

    def setStatus(self, hubId, status):
        hub = self.hubs[hubId]
        status = self._setAttributes(hub, {'fanc': status})
        return status

    def _setAttributes(self, hub, attrs):
        url = '{}/api/hub/update/attr'.format(self.BASE_URL)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        json_data = {'attr': {}}
        for key in attrs.keys():
            json_data['attr'][key] = attrs[key]

        data = urlencode({'hub':hub['hash'], 'json': json_data})
        r = requests.post(url, data=data, headers=headers)

        if r.status_code == 200:
            print('Attributes updated.')
            return True
        else:
            print('Something went wrong with setting attributes {}'.format(r.text()))
            return False