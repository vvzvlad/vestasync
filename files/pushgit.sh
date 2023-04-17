#!/usr/bin/env sh
apt-mark showmanual > /mnt/data/etc/vestasync/packages
echo $(hostname) > /mnt/data/etc/vestasync/hostname
export GIT_AUTHOR_NAME="vestasync_wb_$(hostname)"
export GIT_COMMITTER_NAME="vestasync_wb_$(hostname)"
export LC_TIME=en_GB.UTF-8
cd /mnt/data/etc/ > /dev/null 2>&1 || true
git add . > /dev/null 2>&1 || true
git commit -m "$(date +"%Y-%m-%d %H:%M:%S %z %Z")" > /dev/null 2>&1 || true
git push -u origin master > /dev/null 2>&1 || true

