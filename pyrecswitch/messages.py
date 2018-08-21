#!/usr/bin/env python
# -*- Mode: Python; tab-width: 4 -*-
#
# pyrecswitch - interface for controlling Ankuoo RecSwitch MS6126
# Copyright (C) 2018 Marco Lertora <marco.lertora@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import struct
from Crypto.Cipher import AES

from .exceptions import RSInvalidMessage
from .constants import RSConstants, RSHeaderFlag, RSCommand
from .helpers import unpack_mac_address
from .structures import GPIOStatus, HeartBeat, ModuleInfo, RSDeviceConfig


class RSMessages:
    header_format = '!BB6sB'
    header_length = struct.calcsize(header_format)
    payload_header_format = '!BHBBH'
    message_command_format = '!B'
    payload_header_length = struct.calcsize(payload_header_format)
    default_payload_length = 16

    @staticmethod
    def parse_message(data):
        if len(data) < RSMessages.header_length:
            raise RSInvalidMessage('invalid message length')

        pv, flag, mac_address, payload_length = struct.unpack_from(RSMessages.header_format, data)

        device_config = RSDeviceConfig(unpack_mac_address(mac_address))

        if pv != RSConstants.SOCKET_HEADER_PV:
            raise RSInvalidMessage('invalid message header', data.hex())

        if len(data) < RSMessages.header_length + payload_length:
            raise RSInvalidMessage('invalid message length', data.hex())

        payload = data[RSMessages.header_length:RSMessages.header_length + payload_length]

        if len(payload) != payload_length:
            raise RSInvalidMessage('invalid message length', data.hex())

        if bool(flag & RSHeaderFlag.encrypted):
            decipher = AES.new(device_config.aes_key, AES.MODE_CBC, device_config.aes_iv)
            payload = decipher.decrypt(data[RSMessages.header_length:])

        (reserved,
         message_index,
         device_config.device_type,
         device_config.factory_code,
         device_config.license_data) = struct.unpack_from(RSMessages.payload_header_format, payload)

        message = payload[RSMessages.payload_header_length:]
        command, = struct.unpack_from(RSMessages.message_command_format, message)

        is_reback = bool(flag & RSHeaderFlag.reback)

        if command in (RSCommand.SET_GPIO_STATUS, RSCommand.GET_GPIO_STATUS,
                       RSCommand.REPORT_GPIO_CHANGE):
            flag, fre, duty, res = struct.unpack_from('!BBBB', message, offset=1)
            state = duty == RSConstants.GPIO_FLAG_ON
            return device_config, message_index, command, GPIOStatus(flag=flag, state=state)

        if command == RSCommand.HEART_BEAT:
            if not is_reback:
                return device_config, message_index, command, None

            interval, = struct.unpack_from('!H', message, offset=1)
            return device_config, message_index, command, HeartBeat(interval=interval)

        if command == RSCommand.QUERY_MODULE_INFO:
            if not is_reback:
                return device_config, message_index, command, None

            offset = 1
            response = ModuleInfo()
            for index, name in enumerate(('hw_version', 'sw_version', 'device_name')):
                length, = struct.unpack_from('!B', message, offset=offset)
                value, = struct.unpack_from('!{}s'.format(length), message, offset=offset + 1)
                offset += length + 1
                setattr(response, name, value.decode())
                response.status, = struct.unpack_from('!B', message, offset=offset)

            return device_config, message_index, command, response

        raise RSInvalidMessage('unknown message type: {0:X}'.format(command))

    @staticmethod
    def build_message(device_config, message_command, message_body=b''):
        message_index = RSDeviceConfig.new_message_index()

        message_prefix = struct.pack(RSMessages.message_command_format, message_command)
        payload = RSMessages.build_payload(device_config, message_index, message_prefix + message_body)

        flag = RSHeaderFlag.blank
        if device_config.use_encryption:
            flag |= RSHeaderFlag.encrypted
            cipher = AES.new(device_config.aes_key, AES.MODE_CBC, device_config.aes_iv)
            payload = cipher.encrypt(payload)

        header_pv = RSConstants.SOCKET_HEADER_PV
        mac_address = device_config.binary_mac_address
        data = struct.pack(RSMessages.header_format, header_pv, flag, mac_address, len(payload))
        return message_index, data + payload

    @staticmethod
    def build_payload(device_config, message_index, message):
        if not RSDeviceConfig.min_message_index <= message_index <= RSDeviceConfig.max_message_index:
            raise RSInvalidMessage('invalid message_index, {} - {}'.format(RSDeviceConfig.min_message_index,
                                                                           RSDeviceConfig.max_message_index))

        reserved = RSConstants.SOCKET_HEADER_RESERVED
        data = struct.pack(RSMessages.payload_header_format, reserved, message_index, device_config.device_type,
                           device_config.factory_code, device_config.license_data)
        data = data + message
        data = data.ljust(RSMessages.default_payload_length, bytes([RSConstants.SOCKET_PAYLOAD_PADDING]))
        return data

    @staticmethod
    def get_gpio_status(device_config, flag):
        if not 0 <= flag <= 3:
            raise RSInvalidMessage('invalid flag, 0 - 3')

        message_command = RSCommand.GET_GPIO_STATUS
        message_body = struct.pack('!BBBB', flag, RSConstants.GPIO_FRE, RSConstants.GPIO_FLAG_OFF, RSConstants.GPIO_RES)
        return RSMessages.build_message(device_config, message_command, message_body)

    @staticmethod
    def set_gpio_status(device_config, flag, state):
        message_command = RSCommand.SET_GPIO_STATUS
        state = RSConstants.GPIO_FLAG_ON if state else RSConstants.GPIO_FLAG_OFF
        message_body = struct.pack('!BBBB', flag, RSConstants.GPIO_FRE, state, RSConstants.GPIO_RES)
        return RSMessages.build_message(device_config, message_command, message_body)

    @staticmethod
    def heart_beat(device_config):
        message_command = RSCommand.HEART_BEAT
        return RSMessages.build_message(device_config, message_command)

    @staticmethod
    def query_module_info(device_config):
        message_command = RSCommand.QUERY_MODULE_INFO
        return RSMessages.build_message(device_config, message_command)
