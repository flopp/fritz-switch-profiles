import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

name = "fritz_switch_profiles"

from .fritz_switch_profiles import FritzProfileSwitch