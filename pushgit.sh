#!/usr/bin/env sh
cd /mnt/data/etc/ > /dev/null 2>&1 || true
git add . > /dev/null 2>&1 || true
git commit -m "$(date)" > /dev/null 2>&1 || true
git push -u origin master > /dev/null 2>&1 || true
