# homeassistant-light.merkury
This module is a plugin for homeassistant and Merkury lights, which is a tuya variant, for local control instead of using the Tuya app

This has only been testeed with Merkury innovations 75 watt color lights. These are about $13 at Wal-Mart

This allows you to take control of the lights locally once you have completed initial settup and a little work to get the correct key information. Be free from relying on the Tuya Cloud.

It is based on the pytuya library [https://github.com/clach04/python-tuya] to control the lights. It includes references to all required libraries so they get installed directly by Home Assistant. Specifically it has been tested with hassio in docker on Ubuntu 18.

To use cd to the Home Assistant config directory for your installation (wherever the configuration.yaml file lives) and `mkdir custom_components/light` and copy the merkury.py file into that `<haconfig>/custom_components/light` directory you just created.

Next you will need to get the keys for your device. The best instructions are here: [https://github.com/codetheweb/tuyapi/blob/master/docs/SETUP.md] or here: [https://github.com/clach04/python-tuya/wiki/Setup]

With that wonderful information from the tuyapi CLI or some other proxy, you are ready to update your configuration.yaml (but check your current one, and restart HA first) with an entry like this:

```
- platform: merkury
  devices:
    light1:
      name: light 1
      host: 192.168.0.42
      local_key: xxxxxxxxxxxxxxxx
      device_id: xxxxxxxxxxxxxxxxxxxx
    light2:
      name: light 2
      host: 2.46.0.1
      local_key: xxxxxxxxxxxxxxxx
      device_id: xxxxxxxxxxxxxxxxxxxx
    light3:
      name: light 3
      host: 1.1.2.3
      local_key: xxxxxxxxxxxxxxxx
      device_id: xxxxxxxxxxxxxxxxxxxx
```

Restart and you should be good to go.

At least the Merkury bulbs come up with the hostname ESP_ffffff where ffffff is the last 6 digits of the mac which is also the end of the device_id so once you have the device_id you can find the ip with any IP scanner.

Finally these bulbs only accept one connection at a time. which means that if you are connected with the Tuya App or with one of the other APIs they will reject your http request. Make sure you shut all those down before using this in HA

TODO:
Better update functionality so that HA shows the right color.
Clean up.
Test other Tuya Bulbs and flush out functionality a bit more.

Thanks to all those who contributed projects that influenced this one:
### Related Projects
  * https://github.com/clach04/python-tuya
  * https://github.com/sean6541/tuyaapi Python API to the web api
  * https://github.com/codetheweb/tuyapi node.js
  * https://github.com/Marcus-L/m4rcus.TuyaCore - .NET
  * https://github.com/SDNick484/rectec_status/ - RecTec pellet smokers control (with Alexa skill)

### Acknowledgements

  * Major breakthroughs on protocol work came from https://github.com/codetheweb/tuyapi from the reverse engineering time and skills of codetheweb and blackrozes, additional protocol reverse engineering from jepsonrob and clach04.
  * clach04 and all those that helped him pull together pytuya
  * sean6541 - for initial pytuya PyPi package and Home Assistant support for tuya switches that became the basis for this module <https://github.com/sean6541/tuya-homeassistant>
