#!/usr/bin/env bash
EXCLUDE_PATTERN='(^|/)(\.git($|/)|wb-mqtt-mbgate\.conf$|resolv\.conf$)'

inotifywait -m -r -e close_write,move,create,delete --exclude "$EXCLUDE_PATTERN" --format '%w%f' /mnt/data/etc | while read FILE
do
    echo $(hostname) > /mnt/data/etc/vestasync/hostname
    export GIT_AUTHOR_NAME="vestasync_wb_$(hostname)_inotify"
    export GIT_COMMITTER_NAME="vestasync_wb_$(hostname)_inotify"
    export LC_TIME=en_GB.UTF-8
    cd /mnt/data/etc/
    git add .
    git commit -m "$(date +"%Y-%m-%d %H:%M:%S %z %Z")" # > /dev/null 2>&1 || true
    git push -u origin master
done
