#!/usr/bin/env python3

import asyncio
import socket
import itertools
import json
import struct

import netjson


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


agents = {}


async def agent_connection(reader, writer):

    agent = writer.get_extra_info("peername")
    sock = writer.get_extra_info("socket")

    nj = netjson.NetJson(reader, writer)

    agents[agent] = []
    print(f"Added agent {agent} to agent list")

    while not is_socket_closed(sock):
        await nj.write(agents[agent])
        agents[agent].clear()
        await asyncio.sleep(5)

    print(f"Connectin to agent {agent} has been closed")
    writer.close()
    agents.pop(agent)
    print(f"Removed agent {agent} from agent list")


def pick_agent(host):
    if len(agents):
        return list(agents)[abs(hash(host)) % len(agents)]


async def dispatcher():

    while True:
        with open("hosts") as _:
            hosts = _.read().splitlines()

        jobs = [
            {
                "host": _,
                "device_type": "cisco_ios",
                "username": "vf10netcat1",
                "client_keys": "/home/netcat_backup/.ssh/id_rsa",
                "polls": [{"id": "cpu", "command": "show processes cpu | include CPU", "regex": r"ds: (\d{1,2})"}],
            }
            for _ in hosts
        ]

        for job in jobs:
            if agent := pick_agent(job["host"]):
                if job not in agents[agent]:
                    agents[agent].append(job)
        await asyncio.sleep(1)


async def agent_monitor():

    while True:
        print("Connected agents:")
        for agent in agents:
            print(agent, len(agents[agent]))
        print()
        await asyncio.sleep(1)


async def main():
    server = await asyncio.start_server(agent_connection, "127.0.0.1", 5555)

    addr = server.sockets[0].getsockname()
    print(f"Server waiting for agents on: {addr}")

    # asyncio.create_task(agent_monitor())
    asyncio.create_task(dispatcher())

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
