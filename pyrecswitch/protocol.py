#!/usr/bin/env python
# -*- Mode: Python; tab-width: 4 -*-
#
# pyrecswitch - communication protocol for Lumitek/Ankuoo RecSwitch
# Copyright (C) 2018 Marco Lertora <marco.lertora@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import struct
from Crypto.Cipher import AES

from .constants import Constants, HeaderFlag, RecSwitchCommand
from .helpers import unpack_mac_address
from .structures import GPIOStatus, HeartBeat, ModuleInfo, RecSwitchDeviceConfig


class RecSwitchServerProtocol:

    def __init__(self,):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, remote_address):
        device_config, command, response = RecSwitchProtocol.parse_packet(data)
        self.packet_received(remote_address, device_config, command, response)

    def packet_received(self, remote_address, device_config, command, response):
        raise NotImplementedError


class RecSwitchInvalidPacket(Exception):
    pass


class RecSwitchProtocol:

    header_format = '!BB6sB'
    header_length = struct.calcsize(header_format)
    payload_header_format = '!BHBBH'
    message_command_format = '!B'
    payload_header_length = struct.calcsize(payload_header_format)
    default_payload_length = 16

    @staticmethod
    def parse_packet(data):
        if len(data) < RecSwitchProtocol.header_length:
            raise RecSwitchInvalidPacket('invalid packet length')

        pv, flag, mac_address, payload_length = struct.unpack_from(RecSwitchProtocol.header_format, data)

        device = RecSwitchDeviceConfig(unpack_mac_address(mac_address))

        if pv != Constants.SOCKET_HEADER_PV:
            raise RecSwitchInvalidPacket('invalid packet header', data.hex())

        if len(data) < RecSwitchProtocol.header_length + payload_length:
            raise RecSwitchInvalidPacket('invalid packet length', data.hex())

        payload = data[RecSwitchProtocol.header_length:RecSwitchProtocol.header_length + payload_length]

        if len(payload) != payload_length:
            raise RecSwitchInvalidPacket('invalid packet length', data.hex())

        if bool(flag & HeaderFlag.encrypted):
            decipher = AES.new(device.aes_key, AES.MODE_CBC, device.aes_iv)
            payload = decipher.decrypt(data[RecSwitchProtocol.header_length:])

        (reserved,
         device.message_index,
         device.device_type,
         device.factory_code,
         device.license_data) = struct.unpack_from(RecSwitchProtocol.payload_header_format, payload)

        message = payload[RecSwitchProtocol.payload_header_length:]
        command, = struct.unpack_from(RecSwitchProtocol.message_command_format, message)

        is_reback = bool(flag & HeaderFlag.reback)

        if command in (RecSwitchCommand.SET_GPIO_STATUS, RecSwitchCommand.GET_GPIO_STATUS,
                       RecSwitchCommand.REPORT_GPIO_CHANGE):
            flag, fre, duty, res = struct.unpack_from('!BBBB', message, offset=1)
            state = duty == Constants.GPIO_FLAG_ON
            return device, command, GPIOStatus(flag=flag, state=state)

        if command == RecSwitchCommand.HEART_BEAT:
            if not is_reback:
                return device, command, None

            interval, = struct.unpack_from('!H', message, offset=1)
            return device, command, HeartBeat(interval=interval)

        if command == RecSwitchCommand.QUERY_MODULE_INFO:
            if not is_reback:
                return device, command, None

            offset = 1
            response = ModuleInfo()
            for index, name in enumerate(('hw_version', 'sw_version', 'device_name')):
                length, = struct.unpack_from('!B', message, offset=offset)
                value, = struct.unpack_from('!{}s'.format(length), message, offset=offset + 1)
                offset += length + 1
                setattr(response, name, value.decode())
                response.status, = struct.unpack_from('!B', message, offset=offset)

            return device, command, response

        raise RecSwitchInvalidPacket('unknown message type: {0:X}'.format(command))

    @staticmethod
    def build_packet(device, message_command, message_body=b''):
        device.next_message_index()
        message = RecSwitchProtocol.build_message(message_command, message_body)
        payload = RecSwitchProtocol.build_payload(device, message)

        flag = HeaderFlag.blank
        if device.use_encryption:
            flag |= HeaderFlag.encrypted
            cipher = AES.new(device.aes_key, AES.MODE_CBC, device.aes_iv)
            payload = cipher.encrypt(payload)

        header_pv = Constants.SOCKET_HEADER_PV
        mac_address = device.binary_mac_address
        data = struct.pack(RecSwitchProtocol.header_format, header_pv, flag, mac_address, len(payload))
        return data + payload

    @staticmethod
    def build_payload(device, message):
        if not 1 <= device.message_index <= RecSwitchDeviceConfig.max_message_index:
            raise RecSwitchInvalidPacket('invalid message_index, should be from 1 to 65535')

        reserved = Constants.SOCKET_HEADER_RESERVED
        data = struct.pack(RecSwitchProtocol.payload_header_format, reserved, device.message_index,
                           device.device_type, device.factory_code, device.license_data)
        data = data + message
        data = data.ljust(RecSwitchProtocol.default_payload_length, bytes([Constants.SOCKET_PAYLOAD_PADDING]))
        return data

    @staticmethod
    def build_message(message_command, message_body=b''):
        data = struct.pack(RecSwitchProtocol.message_command_format, message_command)
        return data + message_body

    @staticmethod
    def get_gpio_status(device, flag):
        if not 0 <= flag <= 3:
            raise RecSwitchInvalidPacket('invalid flag, should be from 0 to 3')

        message_command = RecSwitchCommand.GET_GPIO_STATUS
        message_body = struct.pack('!BBBB', flag, Constants.GPIO_FRE, Constants.GPIO_FLAG_OFF, Constants.GPIO_RES)
        return RecSwitchProtocol.build_packet(device, message_command, message_body)

    @staticmethod
    def set_gpio_status(device, flag, state):
        message_command = RecSwitchCommand.SET_GPIO_STATUS
        state = Constants.GPIO_FLAG_ON if state else Constants.GPIO_FLAG_OFF
        message_body = struct.pack('!BBBB', flag, Constants.GPIO_FRE, state, Constants.GPIO_RES)
        return RecSwitchProtocol.build_packet(device, message_command, message_body)

    @staticmethod
    def heart_beat(device):
        message_command = RecSwitchCommand.HEART_BEAT
        return RecSwitchProtocol.build_packet(device, message_command)

    @staticmethod
    def query_module_info(device):
        message_command = RecSwitchCommand.QUERY_MODULE_INFO
        return RecSwitchProtocol.build_packet(device, message_command)
