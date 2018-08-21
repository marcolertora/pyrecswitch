import sys
import socket
import time

from pyrecswitch import RSDeviceConfig, RSMessages


if __name__ == '__main__':

    if len(sys.argv) < 3:
        print('usage: {} ip-address mac-address'.format(sys.argv[0]))
        sys.exit(1)

    flag = 0
    interval = 2

    remote_ip_address = sys.argv[1]
    remote_mac_address = sys.argv[2]
    remote_port = RSDeviceConfig.default_udp_port

    local_ip_address = '0.0.0.0'
    local_port = RSDeviceConfig.default_udp_port

    device_config = RSDeviceConfig(remote_mac_address)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((local_ip_address, local_port))

    def send_message(message_index, message):
        _ = sock.sendto(message, (remote_ip_address, remote_port))
        return receive_message(message_index)

    def receive_message(message_index, size=8192):
        data, _ = sock.recvfrom(size)
        response_device_config, response_message_index, response_command, response = RSMessages.parse_message(data)

        if message_index != response_message_index:
            return receive_message(message_index, size)

        return response

    # get module info
    ret = send_message(*RSMessages.query_module_info(device_config))
    print('QUERY MODULE INFO: device_name={0.device_name} sw_version={0.sw_version}'.format(ret))

    # get relay status
    ret = send_message(*RSMessages.get_gpio_status(device_config, flag=flag))
    print('GET GPIO STATUS: flag={0.flag} state={0.state}'.format(ret))

    # set relay status to inverse value
    ret = send_message(*RSMessages.set_gpio_status(device_config, flag=flag, state=not ret.state))
    print('SET GPIO STATUS: flag={0.flag} state={0.state}'.format(ret))

    time.sleep(interval)

    # set relay status to initial value
    ret = send_message(*RSMessages.set_gpio_status(device_config, flag=flag, state=not ret.state))
    print('SET GPIO STATUS: flag={0.flag} state={0.state}'.format(ret))

    sock.close()
