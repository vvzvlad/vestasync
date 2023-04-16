#!/usr/bin/env sh
echo $(hostname) > /mnt/data/etc/vestasync/hostname
export GIT_AUTHOR_NAME="vestasync_wb_$(hostname)"
export GIT_COMMITTER_NAME="vestasync_wb_$(hostname)"
cd /mnt/data/etc/ > /dev/null 2>&1 || true
git add . > /dev/null 2>&1 || true
git commit -m "$(date)" > /dev/null 2>&1 || true
git push -u origin master > /dev/null 2>&1 || true
