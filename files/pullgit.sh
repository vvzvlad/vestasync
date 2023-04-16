#!/usr/bin/env sh
git config --global user.name vestasync_wb_$(hostname)
git config --global user.email "vestasync@fake.mail"
cd /mnt/data/etc/
git fetch > /dev/null 2>&1 || true
git pull > /dev/null 2>&1 || true
