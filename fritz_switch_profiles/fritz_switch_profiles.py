#!/usr/bin/env python3

# Copyright 2018 Florian Pigorsch & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

import argparse
import hashlib
import lxml.etree
import lxml.html
import re
import requests
import sys
import logging


class FritzProfileSwitch:
    def __init__(self, url, user, password):
        self.url = url
        self.sid = self.login(user, password)
        self.profiles = []
        self.devices = []
        self.fetch_profiles()
        self.fetch_devices()
        self.fetch_device_profiles()

    def get_sid_challenge(self, url):
        r = requests.get(url, allow_redirects=True)
        data = lxml.etree.fromstring(r.content)
        sid = data.xpath('//SessionInfo/SID/text()')[0]
        challenge = data.xpath('//SessionInfo/Challenge/text()')[0]
        return sid, challenge

    def login(self, user, password):
        logging.info("LOGGING IN TO FRITZ!BOX AT {}...".format(self.url))
        sid, challenge = self.get_sid_challenge(self.url + '/login_sid.lua')
        if sid == '0000000000000000':
            md5 = hashlib.md5()
            md5.update(challenge.encode('utf-16le'))
            md5.update('-'.encode('utf-16le'))
            md5.update(password.encode('utf-16le'))
            response = challenge + '-' + md5.hexdigest()
            url = self.url + '/login_sid.lua?username=' + user + '&response=' + response
            sid, challenge = self.get_sid_challenge(url)
        if sid == '0000000000000000':
            raise PermissionError('Cannot login to {} using the supplied credentials.'.format(self.url))
        return sid

    def fetch_device_profiles(self):
        logging.info('FETCHING DEVICE PROFILES...')
        data = {'xhr': 1, 'sid': self.sid, 'cancel': '', 'oldpage': '/internet/kids_userlist.lua'}
        url = self.url + '/data.lua'
        r = requests.post(url, data=data, allow_redirects=True)
        html = lxml.html.fromstring(r.content)
        for row in html.xpath('//table[@id="uiDevices"]/tr'):
            td = row.xpath('td')
            if (not td) or (len(td) != 5):
                continue
            select = td[3].xpath('select')
            if not select:
                continue
            id2 = select[0].xpath('@name')[0].split(':')[1]
            device_name = td[0].xpath('span/text()')[0]
            profile = select[0].xpath('option[@selected]/@value')[0]
            self.merge_device(device_name, id2, profile)

    def merge_device(self, name, id2, profile):
        multi = False
        found = -1
        for index, device in enumerate(self.devices):
            if id2 == device['id1']:
                if found >= 0:
                    multi = True
                found = index
            elif name == device['name']:
                if found >= 0:
                    multi = True
                found = index
        if found < 0:
            logging.info('  NO MATCH FOR {:16} {}'.format(id2, name))
        elif multi:
            logging.info('  MULTIPLE MATCHES FOR {:16} {}'.format(id2, name))
        else:
            if self.devices[found]['id1'] != id2:
                self.devices[found]['id2'] = id2
            self.devices[found]['profile'] = profile

    def get_device(self, device_id):
        for device in self.devices:
            if device['id1'] == device_id or device['id2'] == device_id:
                return device
        return None

    def get_profile(self, profile_id):
        for profile in self.profiles:
            if profile['id'] == profile_id:
                return profile
        return None

    def fetch_devices(self):
        logging.info('FETCHING DEVICES...')
        data = {'xhr': 1, 'sid': self.sid, 'no_sidrenew': '', 'page': 'netDev'}
        url = self.url + '/data.lua'
        r = requests.post(url, data=data, allow_redirects=True)
        j = r.json()
        self.devices = []
        for device in j['data']['active']:
            self.devices.append({
                'name': device['name'],
                'id1': device['UID'],
                'id2': None,
                'profile': None,
                'active': True
            })
        for device in j['data']['passive']:
            self.devices.append({
                'name': device['name'],
                'id1': device['UID'],
                'id2': None,
                'profile': None,
                'active': False
            })

    def fetch_profiles(self):
        logging.info('FETCHING AVAILABLE PROFILES...')
        data = {'xhr': 1, 'sid': self.sid, 'no_sidrenew': '', 'page': 'kidPro'}
        url = self.url + '/data.lua'
        r = requests.post(url, data=data, allow_redirects=True)
        html = lxml.html.fromstring(r.content)
        self.profiles = []
        for row in html.xpath('//table[@id="uiProfileList"]/tr'):
            profile_name = row.xpath('td[@class="name"]/span/text()')
            if not profile_name:
                continue
            profile_name = profile_name[0]
            profile_id = row.xpath('td[@class="btncolumn"]/button[@name="edit"]/@value')[0]
            self.profiles.append({'name': profile_name, 'id': profile_id})

    def get_devices(self):
        return sorted(self.devices, key=lambda x: x['name'].lower())

    def print_devices(self):
        print('\n{:16} {:16} {}'.format('DEVICE_ID', 'PROFILE_ID', 'DEVICE_NAME'))
        for device in sorted(self.devices, key=lambda x: x['name'].lower()):
            print('{:16} {:16} {}{}'.format(
                device['id1'],
                device['profile'] if device['profile'] else 'NONE',
                device['name'],
                '' if device['active'] else ' [NOT ACTIVE]'))

    def get_profiles(self):
        return self.profiles

    def print_profiles(self):
        print('\n{:16} {}'.format('PROFILE_ID', 'PROFILE_NAME'))
        for profile in self.profiles:
            print("{:16} {}".format(profile['id'], profile['name']))

    def set_profiles(self, deviceProfiles):
        logging.info('\nUPDATING DEVICE PROFILES...')
        data = {'xhr': 1, 'sid': self.sid, 'apply': '', 'oldpage': '/internet/kids_userlist.lua'}
        updates = 0
        for device_id, profile_id in deviceProfiles:
            device = self.get_device(device_id)
            if not device:
                logging.error('  CANNOT IDENTIFY DEVICE {}'.format(device_id))
                continue
            profile = self.get_profile(profile_id)
            if not profile:
                logging.error('  CANNOT IDENTIFY PROFILE {}'.format(profile_id))
                continue
            logging.info('  CHANGING PROFILE OF {}/{} TO {}/{}'.format(
                device_id, device['name'], profile_id, profile['name']))
            if device['id2']:
                device_id = device['id2']
            updates += 1
            data['profile:' + device_id] = profile_id
        if updates > 0:
            url = self.url + '/data.lua'
            requests.post(url, data=data, allow_redirects=True)


def parse_kv(s):
    if not re.match('^[^=]+=[^=]+$', s):
        raise argparse.ArgumentTypeError("Invalid format: '{}'.".format(s))
    return s.split('=')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', metavar='URL', type=str, default='http://fritz.box',
                        help='The URL of your Fritz!Box; default: http://fritz.box')
    parser.add_argument('--user', metavar='USER', type=str, default='',
                        help='Login username; default: empty')
    parser.add_argument('--password', metavar='PASSWORD', type=str, required=True,
                        help='Login password')
    parser.add_argument('--list-devices', dest='listdevices', action='store_true',
                        help='List all known devices')
    parser.add_argument('--list-profiles', dest='listprofiles', action='store_true',
                        help='List all available profiles')
    parser.add_argument('deviceProfiles', nargs='*', metavar='DEVICE=PROFILE',
                        type=parse_kv,
                        help='Desired device to profile mapping')
    args = parser.parse_args()

    fps = FritzProfileSwitch(args.url, args.user, args.password)
    if args.listdevices:
        fps.print_devices()
    if args.listprofiles:
        fps.print_profiles()
    if args.deviceProfiles:
        fps.set_profiles(args.deviceProfiles)


if __name__ == '__main__':
    try:
        main()
    except requests.exceptions.ConnectionError as e:
        logging.error('Failed to connect to Fritz!Box')
        logging.error(e)
        sys.exit(1)
    except PermissionError as e:
        logging.error(e)
        sys.exit(1)
