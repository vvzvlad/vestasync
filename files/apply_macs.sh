#!/bin/bash
macs_dir="/mnt/data/etc/vestasync/macs"

for mac_file in "$macs_dir"/*; do
    ifname=$(basename "$mac_file")
    if [ -f "$mac_file" ]; then
        mac_address=$(cat "$mac_file")
        ip link set "$ifname" address "$mac_address"
    fi
done
