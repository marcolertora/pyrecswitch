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

from enum import IntEnum


class RecSwitchCommand(IntEnum):
    SET_GPIO_STATUS = 0x01
    GET_GPIO_STATUS = 0x02
    REPORT_GPIO_CHANGE = 0x06
    HEART_BEAT = 0x61
    QUERY_MODULE_INFO = 0x62


class HeaderFlag(IntEnum):
    blank = 0b00000000
    reback = 0b00000010
    locked = 0b00000100
    encrypted = 0b01000000


class Constants(IntEnum):
    SOCKET_HEADER_PV = 0x01
    SOCKET_HEADER_RESERVED = 0x00
    SOCKET_PAYLOAD_PADDING = 0x04

    GPIO_FLAG_ON = 0xFF
    GPIO_FLAG_OFF = 0x00
    GPIO_RES = 0xFF
    GPIO_FRE = 0x00
