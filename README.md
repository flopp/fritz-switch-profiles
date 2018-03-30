[![Build Status](https://travis-ci.org/flopp/fritz-switch-profiles.svg?branch=master)](https://travis-ci.org/flopp/fritz-switch-profiles)
![License MIT](https://img.shields.io/badge/license-MIT-lightgrey.svg?style=flat)

# fritz-switch-profiles
A (Python) script to remotely set device profiles of an AVM Fritz!Box

## Installation

```
git clone https://github.com/flopp/fritz-switch-profiles.git
cd fritz-switch-profiles
virtualenv -p python3 env
source env/bin/activate
pip install -r requirements.txt
```

## Usage

```
usage: fritz-switch-profiles.py [-h] [--url URL] [--user USER] --password
                                PASSWORD [--list-devices] [--list-profiles]
                                [DEVICE=PROFILE [DEVICE=PROFILE ...]]

positional arguments:
  DEVICE=PROFILE       Desired device to profile mapping

optional arguments:
  -h, --help           show this help message and exit
  --url URL            The URL of your Fritz!Box; default: http://fritz.box
  --user USER          Login username; default: empty
  --password PASSWORD  Login password
  --list-devices       List all known devices
  --list-profiles      List all available profiles
```

1. Determine the ID of the device, whose profile you want to change

```
./fritz-switch-profiles.py --password YOURPASSWORD --list-devices
```
->
```
LOGGING IN TO FRITZ!BOX AT http://fritz.box...
QUERYING DEVICES...
landevice5007    android-1234567890123456 [not active]
landevice6494    my kid's iphone
landevice5006    Chromecast
...
```

2. Determine the available profiles
```
./fritz-switch-profiles.py --password YOURPASSWORD --list-profiles
```
->
```
LOGGING IN TO FRITZ!BOX AT http://fritz.box...
QUERYING PROFILES...
filtprof1        Standard
filtprof2        Gast
filtprof3        UnbeschrÃ¤nkt
filtprof4        Gesperrt 
```

3. Actually change the profiles
```
./fritz-switch-profiles.py --password YOURPASSWORD landevice6494=filtprof4
```
->
```
LOGGING IN TO FRITZ!BOX AT http://fritz.box...
UPDATING DEVICE PROFILES...
CHANGING PROFILE OF landevice6494 TO filtprof4
```

Note that you may change the profiles of multiple devices at once by supplying multiple `DEVICE=PROFILE` pairs on the command line.

## License
[MIT](https://github.com/flopp/fritz-switch-profiles/blob/master/LICENSE) &copy; 2018 Florian Pigorsch & contributors
