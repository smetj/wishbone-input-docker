#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  __init__.py
#
#  Copyright 2017 Jelle Smet <development@smetj.net>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from gevent import monkey; monkey.patch_all()
from gevent import sleep
from wishbone import Actor
from wishbone import Event
import docker
from json import loads as load_json


class DockerIn(Actor):

    '''**Consumes Docker container events and logs.**

    Subscribes to the Docker runtime and consumes events and logs.

    Container logs have following format:

        {"log": "2017-02-05T12:22:13 wishbone[1]: error switch: Module has no queue three.", "container_name": "test"}

    Container events keep Docker's standard


    Parameters:

        - base_url(str)("unix://var/run/docker.sock")
           |  The Docker host

        - auto_follow(bool)(True)
           |  When True automatically starts to tail

    Queues:

        - events
           |  The Docker runtime events.

        - container_stdout
           |  The A description of the queue
    '''

    def __init__(self, actor_config, base_url="unix://var/run/docker.sock", auto_follow=True):
        Actor.__init__(self, actor_config)

        self.pool.createQueue("events")
        self.pool.createQueue("container_stdout")

        self.log_listeners = {}

    def preHook(self):
        self.docker_client = docker.DockerClient(base_url=self.kwargs.base_url)
        self.sendToBackground(self.consumeDockerEvents)

        if self.kwargs.auto_follow:
            self.logging.debug("auto_follow turned on.  Automatically tailing logs of all containers.")
            for container in self.docker_client.containers.list():
                self.sendToBackground(self.setupContainerLogListener, container.name)

    def consumeDockerEvents(self):
        while self.loop():
            try:
                for event in self.docker_client.events():
                    event = load_json(event)
                    if self.kwargs.auto_follow and event["Type"] == "container" and event["status"] == "start":
                        self.sendToBackground(self.setupContainerLogListener, event["Actor"]["Attributes"]["name"])
                    self.submit(Event(event), self.pool.queue.events)
            except Exception as err:
                self.logging.error("Event listener stopped. Reason: %s. Will try to reconnect after 3 seconds." % (err))
                sleep(3)

    def setupContainerLogListener(self, name):
        while self.loop():
            try:
                container = self.docker_client.containers.get(name)
                if container.status == "running":
                    self.logging.info("Collecting logs of container '%s'." % (name))
                    for log in container.attach(stream=True):
                        if log == '':
                            break
                        else:
                            data = {"container_name": name, "log": log.rstrip()}
                            self.submit(Event(data), self.pool.queue.container_stdout)
                else:
                    self.logging.warning("Container '%s' entered '%s' state.  Log listener stops." % (container.name, container.status))
                    #todo(smetj): I guess in the long run this might become memory leaky because long running wishbone processes processing
                    #             many container lifecycles would result into <Actor.greenlets> to be full with stopped greenlets.
                    #             this problem needs to be tackled in the <Wishbone.Actor> module
                    return

            except Exception as err:
                self.logging.error("Failed to setup stdout container listener for '%s'. Reason: %s.  Will setup again after 3 seconds." % (name, err))
                sleep(3)

