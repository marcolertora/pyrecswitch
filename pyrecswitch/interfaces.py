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

import asyncio

from .constants import RSCommand
from .exceptions import RSTimeoutError, RSTransportError, RSNetworkError
from .messages import RSMessages
from .structures import RSDeviceConfig


class RSProtocol(asyncio.DatagramProtocol):

    def __init__(self, parent, timeout_interval=5):
        self.parent = parent
        self.transport = None
        self.messages = dict()
        self.timeout_interval = timeout_interval

    def connection_made(self, transport):
        self.transport = transport

    def has_transport(self):
        return self.transport is not None

    def datagram_received(self, datagram, remote_address):
        asyncio.ensure_future(self.datagram_process(datagram))

    async def datagram_process(self, datagram):
        device_config, message_index, command, response = RSMessages.parse_message(datagram)

        if message_index in self.messages:
            future, timeout = self.messages.pop(message_index)
            future.set_result(response)
            timeout.cancel()
            return

        device = self.parent.devices.get(device_config.mac_address)

        if command == RSCommand.REPORT_GPIO_CHANGE:
            if device and device.report_gpio_change:
                await device.report_gpio_change(response)

    def timeout(self, message_index):
        future, timeout = self.messages.pop(message_index)
        future.set_exception(RSTimeoutError)
        timeout.cancel()

    def send_packet(self, message_index, packet, ip_address, port):
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        if self.transport:
            self.transport.sendto(packet, (ip_address, port))
            timeout = loop.call_later(self.timeout_interval, self.timeout, message_index)
            self.messages[message_index] = (future, timeout)
        else:
            future.set_exception(RSTransportError)
        return future


class RSDevice:

    def __init__(self, parent, mac_address, ip_address, port=None, start_heart_beat_loop=True):
        self.parent = parent
        self.port = port if port else RSDeviceConfig.default_udp_port
        self.ip_address = ip_address
        self.device_config = RSDeviceConfig(mac_address)
        self.heart_beat_interval = 15
        self.report_gpio_change = None

        if start_heart_beat_loop:
            asyncio.ensure_future(self.heart_beat_loop())

    async def heart_beat_loop(self):
        try:
            ret = await self.heart_beat()
            interval = ret.interval
        except RSNetworkError:
            interval = self.heart_beat_interval

        await asyncio.sleep(interval)
        await self.heart_beat_loop()

    async def heart_beat(self):
        return await self.send_packet(*RSMessages.heart_beat(self.device_config))

    async def query_module_info(self):
        return await self.send_packet(*RSMessages.query_module_info(self.device_config))

    async def get_gpio_status(self):
        return await self.send_packet(*RSMessages.get_gpio_status(self.device_config, flag=0))

    async def set_gpio_status(self, state):
        return await self.send_packet(*RSMessages.set_gpio_status(self.device_config, flag=0, state=state))

    def send_packet(self, message_index, packet):
        return self.parent.datagram.send_packet(message_index, packet, self.ip_address, self.port)


class RSNetwork:

    def __init__(self):
        self.devices = dict()
        self.datagram = RSProtocol(self)

    def create_datagram_endpoint(self, loop=None, local_ip_address=None, local_port=None):
        loop = loop if loop else asyncio.get_event_loop()
        local_ip_address = local_ip_address if local_ip_address else '0.0.0.0'
        local_port = local_port if local_port else RSDeviceConfig.default_udp_port
        return loop.create_datagram_endpoint(lambda: self.datagram, local_addr=(local_ip_address, local_port))

    def register_device(self, mac_address, ip_address):
        device = RSDevice(self, mac_address, ip_address)
        self.devices[mac_address] = device
        return device

    def unregister_device(self, mac_address):
        del self.devices[mac_address]

    def get_device(self, mac_address):
        return self.devices[mac_address]
