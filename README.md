# mqtt-notify
MQTT to Desktop Notification script, for using with Home Assistant [MQTT Notifications](https://www.home-assistant.io/examples/notify.mqtt/) service.

[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](http://perso.crans.org/besson/LICENSE.html)

## What
`mqtt-notify.py` takes those messages and turns them into [desktop notifications](https://developer.gnome.org/notification-spec/).

## How
`mqtt-notify.py` uses
* [paho](https://www.eclipse.org/paho/) to access the MQTT broker
* [libnotify](https://gitlab.gnome.org/GNOME/libnotify) to make desktop notifications
* [libsecret](https://wiki.gnome.org/Projects/Libsecret) to store and retrieve passwords
* [dbus-python](https://dbus.freedesktop.org/doc/dbus-python/) and [glib](https://gitlab.gnome.org/GNOME/glib/) to run the main loop and track notification closures
 
## Setup
`mqtt-notify.py` can be run as a [systemd](https://www.freedesktop.org/wiki/Software/systemd/) user service or started manually.

### Installation

```sh
$ mkdir -p ~/.local/bin
$ cp mqtt-notify.py ~/.local/bin
$ mkdir -p ~/.config/systemd/user/
$ cp mqtt-notify.service ~/.config/systemd/user/
```

### Configuration

A simple example configuration file is available at `config`. Copy and modify to suit your needs.
```sh
$ mkdir -p  ~/.config/mqtt-notify/
$ cp config.example ~/.config/mqtt-notify/config
```

#### Password
The user's MQTT authentication password is stored with `libsecret` and will be looked up via the username and the hostname stored in `config`. Add the password to the `libsecret` database.

```sh
$ secret-tool store --label="mqtts://example.com" user myuser service mqtt host example.com
Password: **********
```

### Home Assistant configuration
Use the example script provided in the file ha-script.yaml


### Usage
#### On the client
##### As a user service
```sh
$ systemctl --user daemon-reload
$ systemctl --user enable --now mqtt-notify
```

##### Manual
(Assumes that `~/.local/bin` is in your `$PATH`)

```sh
$ mqtt-notify.py -c ~/.config/mqtt-notify/config
```

#### On Home Assistant
Invoke the notification using this service call

```yaml
service: script.notify_linux_desktop
data:
  message: Hello World
```
