Wunzee - Installation
============


## Hardware
Put everything together:

![Wunzee Hardware](images/hardware.png)

*Do not insert the empty sd card nor power your device on.*


## 1. Preparations 
- download [Raspberry Pi Imager](https://www.raspberrypi.org/blog/raspberry-pi-imager-imaging-utility)
- select Raspberry Pi OS Lite (Raspberry Pi OS (other) -> Raspberry Pi OS Lite (32-bit)) and your microSD
- click on the settings wheel and configure at least:
  - enable SSH (with password access)
  - create user and password (and remember!)
  - Wifi
- click write

## 2. Raspberry Pi
- put the sd card in the raspberry and power it on
- your raspberry will need a few minutes to power on and connect to your network
- use a network scanner or look into your router to find the IP address of your raspberry [How to Find your IP Address](https://www.raspberrypi.com/documentation/computers/remote-access.html#how-to-find-your-ip-address)
- connect to using a ssh client (Windows: [Putty](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html), Linux / OS X: build-in shell) it with the ip you just found out - user and password as inserted above.

## 3. first steps on device
- load the update list: `sudo apt update`
- update the device: `sudo apt upgrade`

## 4. install python and dependencies
- `sudo apt install python3 python3-numpy python3-qrcode python3-serial python3-requests python3-pip python3-git`
- `pip3 install vincenty` (it takes a while, wait a minute)


## 5. display driver installation
- `sudo raspi-config` and choose `Interface Options -> SPI -> Yes`

## 6. install wunzee via github
- install git: `sudo apt install git`
- install wunzee from github: `git clone https://github.com/cixio/wunzee.git`
- run wunzee: `python wunzee/wunzee.py` (just for testing, quit with strg + c)

## 7. autostart wunzee on power on and restart when crashed
- install supervisor: `sudo apt install supervisor`
- copy config file `sudo cp wunzee/wunzee.conf /etc/supervisor/conf.d/wunzee.conf`
- (if you do not use normal path for installation, the path in wunzee.conf must be adapted)
- reload config `sudo supervisorctl reload`
