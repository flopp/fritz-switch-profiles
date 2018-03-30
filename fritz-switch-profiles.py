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


class FritzProfileSwitch:
    def __init__(self, url, user, password):
        self.url = url
        self.sid = self.login(user, password)

    def get_sid_challenge(self, url):
        r = requests.get(url, allow_redirects=True)
        data = lxml.etree.fromstring(r.content)
        sid = data.xpath('//SessionInfo/SID/text()')[0]
        challenge = data.xpath('//SessionInfo/Challenge/text()')[0]
        return sid, challenge

    def login(self, user, password):
        print("LOGGING IN TO FRITZ!BOX AT {}...".format(self.url))
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

    def get_available_profiles(self):
        data = {'xhr': 1, 'sid': self.sid, 'no_sidrenew': '', 'page': 'kidPro'}
        url = self.url + '/data.lua'
        r = requests.post(url, data=data, allow_redirects=True)
        html = lxml.html.fromstring(r.content)
        for row in html.xpath('//table[@id="uiProfileList"]/tr'):
            profile_name = row.xpath('td[@class="name"]/span/text()')
            if not profile_name:
                continue
            profile_name = profile_name[0]
            profile_id = row.xpath('td[@class="btncolumn"]/button[@name="edit"]/@value')[0]
            print("{:16} {}".format(profile_id, profile_name))

    def get_available_devices(self):
        data = {'xhr': 1, 'sid': self.sid, 'no_sidrenew': '', 'page': 'netDev'}
        url = self.url + '/data.lua'
        r = requests.post(url, data=data, allow_redirects=True)
        j = r.json()
        devices = []
        for device in j['data']['active']:
            devices.append((device['UID'], device['name'], True))
        for device in j['data']['passive']:
            devices.append((device['UID'], device['name'], False))
        for device, name, active in sorted(devices, key=lambda x: x[1].lower()):
            print("{:16} {}{}".format(device, name, "" if active else " [not active]"))

    def set_profiles(self, deviceProfiles):
        data = {'xhr': 1, 'sid': self.sid, 'apply': '', 'oldpage': '/internet/kids_userlist.lua'}
        for device, profile in deviceProfiles:
            print("CHANGING PROFILE OF {} TO {}".format(device, profile))
            data['profile:' + device] = profile
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
    parser.add_argument('deviceProfiles', nargs='*', metavar='DEVICE=PROFILE', type=parse_kv,
                        help='Desired device to profile mapping')
    args = parser.parse_args()

    fps = FritzProfileSwitch(args.url, args.user, args.password)
    if args.listdevices:
        print("QUERYING DEVICES...")
        fps.get_available_devices()
    if args.listprofiles:
        print("QUERYING PROFILES...")
        fps.get_available_profiles()
    if args.deviceProfiles:
        print("UPDATING DEVICE PROFILES...")
        fps.set_profiles(args.deviceProfiles)


if __name__ == '__main__':
    try:
        main()
    except requests.exceptions.ConnectionError as e:
        print('Failed to connect to Fritz!Box')
        print(e)
        sys.exit(1)
    except PermissionError as e:
        print(e)
        sys.exit(1)
