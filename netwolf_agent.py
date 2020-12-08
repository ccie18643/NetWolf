#!/usr/bin/env python3

import asyncio
import netdev
import socket
import struct
import re
import json
import time

from socket import gaierror
from asyncssh.misc import PermissionDenied, ConnectionLost
from netdev.exceptions import DisconnectError
from asyncio.exceptions import TimeoutError
from os import system
import multiprocessing


def is_socket_closed(sock):
    try:
        # this will try to read bytes without blocking and also without removing them from buffer (peek only)
        data = sock.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
        if len(data) == 0:
            return True
    except BlockingIOError:
        return False  # socket is open and reading from it would block
    except ConnectionResetError:
        return True  # socket was closed for some other reason
    return False


def find_regex_ml(text, regex, hint=None, optional=True):
    """ Find single or multiple values per each of the lines of text. Uses regex grouping mechanism to mark interesting values. """

    if hint:
        if optional and hint not in text:
            return []
        if not (text_lines := [_ for _ in text.split("\n") if hint in _]):
            return []
    else:
        text_lines = text.split("\n")
    cregex = re.compile(regex)
    return [_.groups() if len(_.groups()) > 1 else _.group(1) for __ in text_lines if (_ := cregex.search(__.rstrip("\r")))]


workers = {}
results = {}


async def worker(job):
    """ Worker coroutine """

    polls = job.pop("polls")

    try:
        async with netdev.create(**job) as cli:
            while time.time() - workers[job["host"]] < 5:
                results[job["host"]] = {poll["id"]: out for poll in polls if (out := find_regex_ml(await cli.send_command(poll["command"]), poll["regex"])[0])}
                await asyncio.sleep(1)
    except (
        ConnectionLost,
        gaierror,
        ValueError,
        PermissionDenied,
        DisconnectError,
        TimeoutError,
        ConnectionRefusedError,
        netdev.exceptions.TimeoutError,
        IndexError,
    ):
        pass
        
    workers.pop(job["host"])
    results.pop(job["host"], None)


async def start_workers(manager_address, manager_port):
    """ Process function """

    asyncio.create_task(print_results())
    job_buffer = b""

    while True:
        try:
            print(f"Attempting connction to {manager_address}, port {manager_port}")
            reader, writer = await asyncio.open_connection(manager_address, manager_port)
            sock = writer.get_extra_info("socket")

            while not is_socket_closed(sock):
                job_buffer += await reader.read(2048)
                job_len = struct.unpack("!H", job_buffer[0:2])[0]
                if len(job_buffer) < job_len:
                    await asyncio.sleep(0.1)
                    continue

                job = job_buffer[2 : job_len + 2]
                job_buffer = job_buffer[2 + job_len :]
                job = json.loads(job)

                if job["host"] not in workers:
                    asyncio.create_task(worker(job))

                workers[job["host"]] = int(time.time())
                await asyncio.sleep(0.1)

        except ConnectionRefusedError:
            await asyncio.sleep(1)


def start_asyncio(manager_address, manager_port):
    """ Start Asyncio in separate process """

    asyncio.run(start_workers(manager_address, manager_port))


async def print_results():
    """ """

    while True:
        system("clear")
        n = 0
        for host in results:
            print(f"{int(results[host]['cpu']):02}", "", end="" if n % 10 else "\n")
            n += 1
        await asyncio.sleep(1)


def main():
    """ Main program function """

    with open("hosts") as _:
        hostnames = _.read().splitlines()

    multiprocessing.Process(target=start_asyncio, args=("127.0.0.1", 5555)).start()
    # multiprocessing.Process(target=start_asyncio, args=(hostnames,)).start()


if __name__ == "__main__":
    main()
