#!/usr/bin/env bash
apt-mark showmanual > /mnt/data/etc/vestasync/packages
echo $(hostname) > /mnt/data/etc/vestasync/hostname
cd /mnt/data/etc/
git add .
git commit -m "$(date +"%Y-%m-%d %H:%M:%S %z %Z")"
git push -u origin master
