"""
Simple platform to control **SOME** Tuya light devices.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/light.tuya/
"""
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_COLOR_TEMP, ATTR_RGB_COLOR, ATTR_HS_COLOR, ENTITY_ID_FORMAT,
    SUPPORT_BRIGHTNESS, SUPPORT_COLOR, SUPPORT_COLOR_TEMP, Light, PLATFORM_SCHEMA)
    
import homeassistant.util.color as color_util

import voluptuous as vol
#from homeassistant.components.switch import SwitchDevice, PLATFORM_SCHEMA
from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_ID, CONF_LIGHTS, CONF_FRIENDLY_NAME, CONF_ICON, CONF_DEVICES)
import homeassistant.helpers.config_validation as cv
from time import (time, sleep)
from threading import Lock
import logging

REQUIREMENTS = ['pyaes','pytuya==7.0.2' ]

CONF_DEVICE_ID = 'device_id'
CONF_LOCAL_KEY = 'local_key'

DEFAULT_ID = '1'

LIGHT_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_LOCAL_KEY): cv.string,
    vol.Optional(CONF_ID, default=DEFAULT_ID): cv.string
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_ID, default=DEFAULT_ID): cv.string,
    vol.Optional(CONF_DEVICES, default={}):
        vol.Schema({cv.slug: LIGHT_SCHEMA}),
})


_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up of the Tuya light."""
    import pytuya
    devices = config[CONF_DEVICES]
    lights = []
    for name, device_config in devices.items():
      bulb_device = pytuya.BulbDevice(
             device_config.get(CONF_DEVICE_ID),
             device_config.get(CONF_HOST),
             device_config.get(CONF_LOCAL_KEY)
  
      )
      #name = device_config.get(CONF_NAME)
      if not name:
          name = "tuya_"+device_config.get(CONF_DEVICE_ID)
      device_id = device_config.get(CONF_ID)
      if not device_id:
          device_id = device_config.get(CONF_DEVICE_ID)
      icon = device_config.get(CONF_ICON)
      if not icon:
          icon="mdi:lightbulb"
      lights.append(
        TuyaDevice(
            bulb_device,
            name,
            icon,
            device_id  
        )
      )

    add_devices(lights)
    

class TuyaCache:
    """Cache wrapper for pytuya.BulbDevice"""

    def __init__(self, device):
        """Initialize the cache."""
        self._cached_status = ''
        self._cached_status_time = 0
        self._device = device
        self._lock = Lock()

    def __get_status(self):
        for i in range(3):
            try:
                status = self._device.status()
                return status
            except ConnectionError:
                if i+1 == 3:
                    raise ConnectionError("Failed to update status.")

    def set_status(self, state, lightid):
        """Change the Tuya light status and clear the cache."""
        self._cached_status = ''
        self._cached_status_time = 0
        return self._device.set_status(state, lightid)

    def status(self):
        """Get state of Tuya light and cache the results."""
        self._lock.acquire()
        try:
            now = time()
            if not self._cached_status or now - self._cached_status_time > 20:
                self._cached_status = self.__get_status()
                self._cached_status_time = time()
            return self._cached_status
        finally:
            self._lock.release()

class TuyaDevice(Light):
    """Representation of a Tuya light."""

    def __init__(self, device, name, icon, lightid):
        """Initialize the Tuya light."""
        self._device = device
        self._name = name
        self._state = False
        self._icon = icon
        self._lightid = lightid
        
        self._brightness = None
        self._color_temp = None
        self._hs = None
        self._rgb = None
        self._mode = None

    @property
    def hs_color(self) -> tuple:
        """Return the color property."""
        return self._hs
        
    @property
    def colorTemp(self):
        """Get colorTemp of Tuya light."""
        return self._colorTemp
    
    @property
    def name(self):
        """Get name of Tuya light."""
        return self._name

    @property
    def is_on(self):
        """Check if Tuya light is on."""
        return self._state

    @property
    def icon(self):
        """Return the icon."""
        return self._icon
    @property
    def brightness(self):
        """Return the brightness of the light."""
        return int(self._device.brightness())
    @property
    def rgb_color(self):
        """Return the RGB_color of the light."""
        return tuple(map(int, self._device.colour_rgb()))

    def turn_on(self, **kwargs):
        """Turn Tuya light on."""
        for i in range(5):
            try:
                if (ATTR_BRIGHTNESS not in kwargs
                        and ATTR_RGB_COLOR not in kwargs
                        and ATTR_COLOR_TEMP not in kwargs):
                    self._device.set_status(True, self._lightid)
                if ATTR_BRIGHTNESS in kwargs:
                    self._brightness = kwargs[ATTR_BRIGHTNESS]
                    self._device.set_brightness(self._brightness)
                     
                if ATTR_RGB_COLOR in kwargs:
                    rgb = kwargs[ATTR_RGB_COLOR]
                    r = rgb[0]
                    g = rgb[1]
                    b = rgb[2]
                    self._rgb = (r,g,b)
                    self._device.set_colour(r,g,b)
                if ATTR_HS_COLOR in kwargs:
                    h = kwargs[ATTR_HS_COLOR][0]
                    s = kwargs[ATTR_HS_COLOR][1]
                    self._hs = (h,s)
                    if (s <= 1):
                        # this is a white bulb scenario
                        # Merkury bulbs have Warm white LEDs, we need to light them up.
                        #HA uses color temps between 153 and 500 we need 0-255
                        if (self._brightness is None):
                            self._brightness = self.brightness()
                        self._colorTemp = 240
                        #self._mode = 'white'
                        # if we don't set the RGB then HA doesn't see it :-(
                        rgb=(255,255,255)
                        self._device.set_colour(rgb[0],rgb[1],rgb[2])
                        self._device.set_white(self._brightness, self._colorTemp)
                    else:    
                        rgb = color_util.color_hs_to_RGB(h,s)
                        r = rgb[0]
                        g = rgb[1]
                        b = rgb[2]
                        self._device.set_colour(r,g,b)
                if ATTR_COLOR_TEMP in kwargs:
                    #white color temp
                    #HA uses color temps between 153 and 500 we need 0-255
                    self._colorTemp = max(int((kwargs[ATTR_COLOR_TEMP] - 155)/1.35),0)
                    self._device.set_white(self.brightness(),self.colorTemp())
                self._device.set_status(True, self._lightid)
                break
            except (ConnectionError, ConnectionResetError) as e:
                if i+1 == 5:
                    raise ConnectionError("Failed to update status.")
                sleep(.2)
                

    def turn_off(self, **kwargs):
        """Turn Tuya light off."""
        self._device.set_status(False, self._lightid)

    def update(self):
        """Get state of Tuya light."""
        for i in range(5):
            try:
                status = self._device.status()
                print(status)
                self._state = status['dps'][self._lightid]
                #sometimes the status returns just one element in dps. this check prevents that from breaking status updates.
                if (len(status['dps']) > 2):
                  hue = int(status['dps']['5'][7:10], 16)
                  saturation = round(int(status['dps']['5'][10:12], 16)/2.55)
                  self._brightness = status['dps']['3']
                  self._hs = (hue,saturation)
                  r = int(status['dps']['5'][0:2], 16)
                  g = int(status['dps']['5'][2:4], 16)
                  b = int(status['dps']['5'][4:6], 16)
                  self._rgb = (r,g,b)
                  mode = status['dps']['2']
                  self._mode = mode
                  break
            except (ConnectionError, ConnectionResetError) as e:
                if i+1 == 5:
                    raise ConnectionError("Failed to update status.")
                sleep(.2)
              
        ##TODO actually get the Type of light from pytuya

    @property
    def supported_features(self):
        """Flag supported features."""
        supports = SUPPORT_BRIGHTNESS
        supports = supports | SUPPORT_COLOR
        #Merkury color bulbs do not support colorTemp even though the Tuya App allows it.
        #supports = supports | SUPPORT_COLOR_TEMP
        return supports
