from fritz_switch_profiles import FritzProfileSwitch

url = 'http://fritz.box'
user = ''
password = 'mysecurepassword'

fps = FritzProfileSwitch(url, user, password)
devices = fps.get_devices()
profiles = fps.get_profiles()

fps.print_devices()
fps.print_profiles()

profile_for_device = [devices[0]['id1'], profiles[2]['id']]

fps.set_profiles(profile_for_device)