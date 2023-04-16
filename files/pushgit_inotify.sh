#!/usr/bin/env bash
EXCLUDE_PATTERN='(^|/)(\.git($|/)|wb-mqtt-mbgate\.conf$|resolv\.conf$)'

inotifywait -m -r -e close_write,move,create,delete --exclude "$EXCLUDE_PATTERN" --format '%w%f' /mnt/data/etc | while read FILE
do
    export GIT_AUTHOR_NAME="vestasync_wb_$(hostname)_inotify"
    export GIT_COMMITTER_NAME="vestasync_wb_$(hostname)_inotify"
    cd /mnt/data/etc/
    git add .
    git commit -m "$(date)"
    git push -u origin master
done
