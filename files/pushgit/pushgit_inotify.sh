#!/usr/bin/env bash
export GIT_AUTHOR_NAME="vestasync_wb_$(hostname)"
export GIT_COMMITTER_NAME="vestasync_wb_$(hostname)"
export LC_TIME=en_GB.UTF-8
EXCLUDE_PATTERN='(^|\/)(\.git|packages|hostname|wb-mqtt-mbgate\.conf|resolv\.conf)($|\/)'
inotifywait -m -r -e close_write,move,create,delete --exclude "$EXCLUDE_PATTERN" --format '%w%f' /mnt/data/etc | while read FILE
do
    /usr/local/bin/pushgit.sh
done



