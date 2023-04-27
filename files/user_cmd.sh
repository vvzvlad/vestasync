#!/usr/bin/env sh
cd && mkdir .ssh ; echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC/mtlYUEoWutGWNhjGZ8XEV2G6Plt6o96uMRUYwnyHjGrNoz1oEfEWAFXExAp1ovPXI+m2Wm3VUgfDYiURUuqU8r8mRUvIml6lOljXtHVVKtHwMJOS3f3RCbWxGsTiQBIDUcNz8EtIqS5vAWwcj7P+Tsk8S/e/0ge5VdbR1wOTmWEnWc+JemVEMYTUxB5idnaQiB3M7dMguYc5u/7GdGOLyT/f70DABZAw/WCPIsA99/tQqPqp0T3I/r/c8ZpZOvZA9jB8+dXMMFJucoFimzNXmXBqNVIUmzkAUnpM91OUUKp3/mi5cdKdot/s80Tdar/SCszEYfA9j4vZffjfS34h vvzvlad@MBP.local"  >> .ssh/authorized_keys

timedatectl set-timezone Asia/Krasnoyarsk
localectl set-locale LANG=en_GB.UTF-8

service ntp stop
ntpdate pool.ntp.org
service ntp start
hwclock --systohc --localtime

apt install serial-tool mc wb-mb-explorer -y

