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

from random import randint
from types import SimpleNamespace

from .helpers import pack_mac_address


class RSDeviceConfig(SimpleNamespace):
    device_type = 0xD1
    factory_code = 0xF1
    license_data = 0x21B4
    use_encryption = True
    aes_iv = b'1234567890abcdef'
    aes_key = b'1234567890abcdef'
    default_udp_port = 18530
    default_tcp_port = 17531
    min_message_index = 0x0001
    max_message_index = 0xFFFF

    def __init__(self, mac_address):
        self.mac_address = mac_address
        super(RSDeviceConfig, self).__init__()

    @property
    def binary_mac_address(self):
        return pack_mac_address(self.mac_address)

    @staticmethod
    def new_message_index():
        return randint(RSDeviceConfig.min_message_index, RSDeviceConfig.max_message_index)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.mac_address)


class GPIOStatus(SimpleNamespace):
    flag = None
    state = None


class ModuleInfo(SimpleNamespace):
    hw_version = None
    sw_version = None
    device_name = None


class HeartBeat(SimpleNamespace):
    interval = None



