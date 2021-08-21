#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later

# Relevant API docs:
#   https://pypi.org/project/paho-mqtt/
#   https://lazka.github.io/pgi-docs/#Notify-0.7
#   https://lazka.github.io/pgi-docs/#Secret-1
#   https://lazka.github.io/pgi-docs/#GLib-2.0
#   https://dbus.freedesktop.org/doc/dbus-python/dbus.mainloop.html

import argparse
import configparser
import signal
import sys
import time
import json
from bidict import bidict
import paho.mqtt.client as mqtt
import gi
gi.require_version('Notify', '0.7')
gi.require_version('Secret', '1')
from gi.repository import GLib, Notify, Secret

from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

notification_map = bidict()
icon = None

class Signaler:
    def __init__(self, loop):
        self.loop = loop

    def handler(self, *_):
        self.loop.quit()

def on_connect(client, userdata, flags, rc):
    print("Connected")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(userdata, qos=2)

def on_close(notification):
    del notification_map.inverse[notification]

def on_message(client, userdata, msg):
    global icon
    payload_raw = msg.payload.decode('utf-8')
    #print(f"Handling payload <{payload_raw}>")
    try:
        payload = json.loads(payload_raw)
    except json.JSONDecodeError:
        print(f"Payload <{payload_raw}> is not a valid json")
        return

    payload: dict
    for key in ('title', 'message', 'tag', 'category', 'timeout', 'urgency'):
        payload.setdefault(key, None)
    if payload['message'] is None:
        return

    if payload['title'] is not None:
        summary = payload['title']
        body = payload['message']
    else:
        summary = payload['message']
        body = None

    if (tag := payload['tag']) is not None:
        if tag in notification_map:
            n = notification_map[tag]
            n.update(summary, body, icon)
        else:
            n = Notify.Notification.new(summary, body, icon)
            notification_map[tag] = n
    else:
        n = Notify.Notification.new(summary, body, icon)

    n: Notify.Notification
    if payload['category'] is not None:
        n.set_category(payload['category'])
    if payload['timeout'] is not None:
        n.set_timeout(payload['timeout'])
    if payload['urgency'] is not None:
        n.set_urgency(Notify.Urgency(payload['urgency']))

    n.show()

def on_disconnect(client, userdata, rc):
    print("Disconnected")

def password(user, host):
    # Insert password with secret-tool(1). E.g.,
    #   secret-tool store --label="mqtts://example.com" user myuser service mqtt host example.com

    schema = Secret.Schema.new(
        "org.freedesktop.Secret.Generic",
        Secret.SchemaFlags.NONE,
        {
            "user": Secret.SchemaAttributeType.STRING,
            "service": Secret.SchemaAttributeType.STRING,
            "host": Secret.SchemaAttributeType.STRING,
        }
    )
    attributes = {
        "user": user,
        "service": "mqtt",
        "host": host,
    }

    while (pw := Secret.password_lookup_sync(schema, attributes, None)) is None:
        time.sleep(5)
    return pw

def config(filename):
    with open(filename) as file:
        config = configparser.ConfigParser()
        config.read_file(file)

        cfg = config[configparser.DEFAULTSECT]
        broker = cfg['broker']
        topic = cfg['topic']
        port = int(cfg['port'])
        user = cfg['user']
        icon = cfg.get('icon')
        insecure = bool(cfg.get('insecure', False))

        return user, broker, port, topic, icon, insecure

def main(argv):
    global icon
    loop = GLib.MainLoop()

    do = Signaler(loop)
    signal.signal(signal.SIGINT,  do.handler)
    signal.signal(signal.SIGTERM, do.handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='configuration file',
        type=argparse.FileType('r'), required=True)
    args = parser.parse_args()

    user, broker, port, topic, icon, insecure = config(args.config.name)

    Notify.init('Home Assistant')
    client = mqtt.Client(userdata=topic)

    client.tls_set()
    client.tls_insecure_set(insecure)
    client.username_pw_set(user, password(user, broker))
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.connect_async(broker, port, 60)

    client.loop_start()

    loop.run()

    client.loop_stop()
    client.disconnect()
    Notify.uninit()

if __name__ == '__main__':
    main(sys.argv)
