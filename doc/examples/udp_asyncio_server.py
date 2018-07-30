import sys
import asyncio

from pyrecswitch import RecSwitchDeviceConfig, RecSwitchCommand, RecSwitchProtocol, RecSwitchServerProtocol


class ServerProtocol(RecSwitchServerProtocol):

    def packet_received(self, remote_address, device_config, command, value):
        command = RecSwitchCommand(command).name
        print('Received from {[0]} {.mac_address} {} {}'.format(remote_address, device_config, command, value))


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print('usage: {} ip-address mac-address'.format(sys.argv[0]))
        sys.exit(1)

    remote_ip_address = sys.argv[1]
    remote_mac_address = sys.argv[2]
    remote_port = RecSwitchDeviceConfig.default_udp_port

    local_ip_address = '0.0.0.0'
    local_port = RecSwitchDeviceConfig.default_udp_port

    polling_interval = 5
    loop = asyncio.get_event_loop()
    device_config = RecSwitchDeviceConfig(remote_mac_address)

    def polling():
        # send heart_beat and get_gpio_status
        transport.sendto(RecSwitchProtocol.heart_beat(device_config), (remote_ip_address, remote_port))
        transport.sendto(RecSwitchProtocol.get_gpio_status(device_config, flag=0), (remote_ip_address, remote_port))
        loop.call_later(polling_interval, polling)

    # start server
    listener = loop.create_datagram_endpoint(ServerProtocol, local_addr=(local_ip_address, local_port))
    transport, protocol = loop.run_until_complete(listener)

    # start polling
    loop.call_soon(polling)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        transport.close()
        loop.close()
