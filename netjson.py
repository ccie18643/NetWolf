#!/usr/bin/env python3

import bz2
import json
import struct
import asyncio


class NetJson:
    """ Class supporting sending json compatible structures over network """

    def __init__(self, reader, writer, compression=True):
        """ Class constructor """

        self.reader = reader
        self.writer = writer
        self.compression = compression
        self.socket = writer.get_extra_info("socket")
        self._rx_buffer = b""

    async def socket_read(self):
        """ Read data from socket """

        self._rx_buffer += await self.reader.read(1460)

    async def write(self, message):
        """ Send message """
            
        message = bytes(json.dumps(message), "utf-8")
        if self.compression:
            compressed_message = bz2.compress(message)
            if len(compressed_message) < len(message):
                message = compressed_message
                compressed_flag = True
        self.writer.write(struct.pack("!L?", len(message), compressed_flag) + message) 
        await self.writer.drain()

    async def read(self):
        """ Receive message """

        while len(self._rx_buffer) < 5:
            await asyncio.sleep(0.001)

        message_len, compressed_flag = struct.unpack("!L?", self._rx_buffer[0:5])

        while len(self._rx_buffer) < message_len:
            await asyncio.sleep(0.001)

        message = self._rx_buffer[5 : message_len + 5]
        self._rx_buffer = self._rx_buffer[message_len + 5 :]
        if compressed_flag:
            message = bz2.decompress(message)
        return json.loads(message)


