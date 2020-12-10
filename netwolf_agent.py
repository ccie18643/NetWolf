#!/usr/bin/env python3

import asyncio
import netdev
import re
import time
import multiprocessing

from socket import gaierror
from asyncssh.misc import PermissionDenied, ConnectionLost
from netdev.exceptions import DisconnectError
from asyncio.exceptions import TimeoutError
from os import system
import multiprocessing
import random
import netjson


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
            while workers[job["host"]] > time.time():
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
        OSError,
    ):
        pass

    workers.pop(job["host"])
    results.pop(job["host"], None)


async def start_workers(manager_address, manager_port):
    """ Process function """

    # asyncio.create_task(print_results())

    while True:
        print(f"Attempting connction to {manager_address}, port {manager_port}")

        try:
            nj = netjson.NetJson(*await asyncio.open_connection(manager_address, manager_port))
        except ConnectionRefusedError:
            await asyncio.sleep(1)

        jobs = []

        while not nj.is_socket_closed():

            if _ := await nj.read(blocking=False):
                jobs = _
                # print(f"Received {len(_)} jobs from manager")

            jobs_hosts = set(_["host"] for _ in jobs)
            active_hosts = set(workers)
            batch_hosts = set()

            if jobs_hosts:
                for _ in range(10):
                    if candidate_hosts := list(jobs_hosts - active_hosts - batch_hosts):
                        batch_hosts.add(random.choice(candidate_hosts))

                print("Jobs received:", len(jobs_hosts))
                print("Jobs running:", len(active_hosts))
                print()

                for job in jobs:
                    if job["host"] in batch_hosts:
                        asyncio.create_task(worker(job))
                        workers[job["host"]] = 30
                    elif workers.get(job["host"], None):
                        workers[job["host"]] = time.time() + 15

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

    for _ in range(multiprocessing.cpu_count()):
        multiprocessing.Process(target=start_asyncio, args=("127.0.0.1", 5555)).start()


if __name__ == "__main__":
    main()
