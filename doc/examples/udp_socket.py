import sys
import socket
import time

from pyrecswitch import RecSwitchDeviceConfig, RecSwitchProtocol


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print('usage: {} ip-address mac-address'.format(sys.argv[0]))
        sys.exit(1)

    flag = 0
    interval = 5

    remote_ip_address = sys.argv[1]
    remote_mac_address = sys.argv[2]
    remote_port = RecSwitchDeviceConfig.default_udp_port

    local_ip_address = '0.0.0.0'
    local_port = RecSwitchDeviceConfig.default_udp_port

    device_config = RecSwitchDeviceConfig(remote_mac_address)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((local_ip_address, local_port))

    def send_command(packet):
        _sent = sock.sendto(packet, (remote_ip_address, remote_port))
        return receive_command()

    def receive_command(size=8192):
        data, _remote_address = sock.recvfrom(size)
        response_device_config, response_command, response = RecSwitchProtocol.parse_packet(data)
        # receive packets until message_index match
        if device_config.message_index != response_device_config.message_index:
            return receive_command(size)
        return response

    # get module info
    response = send_command(RecSwitchProtocol.query_module_info(device_config))
    print('Module Info Name: {} Hw: {} Sw: {}'.format(response.device_name, response.hw_version, response.sw_version))

    # get relay status
    response = send_command(RecSwitchProtocol.get_gpio_status(device_config, flag=flag))
    print('Relay #{} State is {}'.format(response.flag, response.state))

    # set relay status to inverse value
    response = send_command(RecSwitchProtocol.set_gpio_status(device_config, flag=flag, state=not response.state))
    print('Set Relay #{} State to {}'.format(response.flag, response.state))

    time.sleep(interval)

    # set relay status to initial value
    response = send_command(RecSwitchProtocol.set_gpio_status(device_config, flag=flag, state=not response.state))
    print('Set Relay #{} State to {}'.format(response.flag, response.state))

    sock.close()
