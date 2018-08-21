# PyRecSwitch

A pure-python interface for controlling **Ankuoo RecSwitch MS6126** without the use of mobile app or the cloud platform. 

List of similar devices that should work:

* Ankuoo MS6126
* Ankuoo REC 4800009
* Lumitek CSW201 NEO WiFi

## Overview

This package provides a high-level interface for controlling the device. This interface has been developed 
using *asyncio*, however, if you prefer to use a different stack you can directly invoke the low-level methods 
to parse and compose the messages needed to communicate with the device.

## How it works

RecSwitch use two different protocols to communicate with the world. The first one is used to talk directly 
with the app mobile when it is in the same network of the device. Instead, the second one is used to talk with its own 
cloud platform to allow the app to control the device when it is in a foreign network. 
*PyRecSwitch* implements the first communication protocol.

Some note about the protocol:

* The communication transport is UDP and the port is 18530.
* The device and the host listen and send message each other to that port.
* The host send a request message to the device, the device receive the request and send back the response to the host.
* The request and the response could be associated through an index reported in both messages.
* Some messages are sent from the device to the broadcast address of its subnet always on the same port. For example, 
the relay status change is notified with a broadcast message.
* Part of the messages are AES encrypted with a fixed key.

## Installation

```bash
pip install pyrecswitch
```

## Usage

First, instantiate the *RSNetwork*.
```
from pyrecswitch import RSNetwork

net = RSNetwork()
```

Generate the datagram endpoint and ensure it a future with *asyncio*.
```
listener = net.create_datagram_endpoint()

transport, protocol = loop.run_until_complete(listener)
```

Register any devices in your network using their own mac-address and ip-address.
```
device = net.register_device('F0:FE:6B:XX:XX:XX', '192.168.X.X')
```

Now, you can access to the device and communicate with it.
```
device = net.get_device('F0:FE:6B:XX:XX:XX')

# get device info
ret = await device.query_module_info()

# get relay status
ret = await device.get_gpio_status()

# set relay on
ret = await device.set_gpio_status(True)
```

That's it!

### Examples

I wrote two simple client examples to explain how the library can be used. Both the examples query the module 
information and toggle the relay status.
   
* **doc/examples/client.py** high-level client interface
* **doc/examples/udp_socket_client.py** low-level methods for generating and parsing messages

## Contributing

Contributions are welcome. Here some useful features that could be developed:

* Device discover
* Device WIFI setup
* Other device commands

## Authors

* [**Marco Lertora**](https://github.com/marcolertora/) -  <marco.lertora@gmail.com>

## Contributors

* [**Gianluigi Tiesi**](https://github.com/sherpya) -  <sherpya@gmail.com>
The one who can find the needle in the haystack, when the needle is an aes key and the haystack is an apk. 

## Disclaimer

This project is the result of reverse engineering work, it has been developed without any relation with the device 
manufacturer. No warranty is provided either by the author or by the manufacturer.  

## License

This project is licensed under the GNU Affero General Public License v3.0 License - see the [LICENSE](LICENSE.md) file for details

## Links

* Hi Flying Chipset HF-LPB100: http://www.hi-flying.com/index.php?route=product/product/show&product_id=113

* Lumitek CSW201 Ankuoo RecSwitch: http://www.lumitek.cn/en/productsd.php?gid=0&pid=1093

* Lumitek Firmware: https://github.com/mys812/hf

* https://github.com/home-assistant/home-assistant/issues/831

* https://github.com/Diagonactic/Ankuoo
