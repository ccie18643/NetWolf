#!/usr/bin/env python3

import bz2
import json
import struct
import asyncio
import socket


class NetJson:
    """ Class supporting sending json compatible structures over network """

    def __init__(self, reader, writer, compression=True):
        """ Class constructor """

        self._reader = reader
        self._writer = writer
        self._socket = writer.get_extra_info("socket")
        self._compression = compression
        self._rx_buffer = b""

        asyncio.create_task(self._read_socket())

    async def _read_socket(self):
        """ Read data into buffer """

        while not self.is_socket_closed():
            _ = await self._reader.read(2048)
            self._rx_buffer += _

    async def write(self, message):
        """ Send message """

        message = bytes(json.dumps(message), "utf-8")
        if compression := self._compression:
            compressed_message = bz2.compress(message)
            if len(compressed_message) < len(message):
                message = compressed_message
            else:
                compression = False

        self._writer.write(struct.pack("!L?", len(message), compression) + message)
        await self._writer.drain()

    async def read(self, blocking=True):
        """ Receive message """

        if blocking:
            while len(self._rx_buffer) < 5:
                await asyncio.sleep(0.001)

            message_len, compression = struct.unpack("!L?", self._rx_buffer[0:5])

            while len(self._rx_buffer) < message_len + 5:
                await asyncio.sleep(0.001)
        else:
            if len(self._rx_buffer) < 5:
                return None

            message_len, compression = struct.unpack("!L?", self._rx_buffer[0:5])

            while len(self._rx_buffer) < message_len + 5:
                return None

        message = self._rx_buffer[5 : message_len + 5]
        self._rx_buffer = self._rx_buffer[message_len + 5 :]

        if compression:
            message = bz2.decompress(message)

        return json.loads(message)

    def is_socket_closed(self):
        """ Chck if socket has been closed by emote peer """

        try:
            return not len(self._socket.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK))
        except BlockingIOError:
            return False
        except ConnectionResetError:
            return True
        return False
