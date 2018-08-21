import sys
import asyncio

from pyrecswitch import RSNetwork, RSNetworkError


async def polling(device):
    try:
        # get module info
        ret = await device.query_module_info()
        print('QUERY MODULE INFO: device_name={0.device_name} sw_version={0.sw_version}'.format(ret))

        # get relay status
        ret = await device.get_gpio_status()
        print('GET GPIO STATUS: flag={0.flag} state={0.state}'.format(ret))

        # set relay status to inverse value
        ret = await device.set_gpio_status(not ret.state)
        print('SET GPIO STATUS: flag={0.flag} state={0.state}'.format(ret))

        await asyncio.sleep(interval)

        # set relay status to initial value
        ret = await device.set_gpio_status(not ret.state)
        print('SET GPIO STATUS: flag={0.flag} state={0.state}'.format(ret))

    except RSNetworkError:
        print('network error occurred, sleep')


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print('usage: {} ip-address mac-address'.format(sys.argv[0]))
        sys.exit(1)

    interval = 2
    remote_ip_address = sys.argv[1]
    remote_mac_address = sys.argv[2]
    loop = asyncio.get_event_loop()

    my_net = RSNetwork()
    listener = my_net.create_datagram_endpoint()
    transport, protocol = loop.run_until_complete(listener)
    my_device = my_net.register_device(remote_mac_address, remote_ip_address)

    loop.run_until_complete(polling(my_device))
