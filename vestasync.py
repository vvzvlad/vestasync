#!/usr/bin/env python3

from fabric import task, Connection
from invoke.exceptions import UnexpectedExit
from io import StringIO
import requests
import argparse
import re
import sys
import datetime
import json


device_user = "root"
gitea_user = "vestasync"
device_short_sn = ""

cmd_parser = argparse.ArgumentParser(description='Process command line arguments.')
cmd_parser.add_argument('--cmd', help='Command (prepare, update, restore)', required=True)
cmd_args = cmd_parser.parse_known_args()

cmd_args = cmd_args[0]

main_parser = argparse.ArgumentParser(description='Process command line arguments.')
if cmd_args.cmd == "restore":
    main_parser.add_argument('--source_hostname', help='Source device hostname', required=True)
else:
    main_parser.add_argument('--device_new_name', help='Device new name', required=True)
main_parser.add_argument('--gitea_address', help='Gitea address string', required=True)
main_parser.add_argument('--gitea_token', help='Gitea token', required=True)
main_parser.add_argument('--device_ip', help='Device IP', required=True)


args = main_parser.parse_known_args()
args = args[0]



def parse_address(address):
    pattern = r'^(?P<protocol>http|https)://(?P<host>[^:]+):(?P<port>\d+)(/.*|)$'
    match = re.match(pattern, address)
    if match:
        return match.group('protocol'), match.group('host'), match.group('port')
    else:
        raise ValueError("Invalid address format")


def get_short_sn(c):
    global device_short_sn
    device_short_sn = c.run('wb-gen-serial -s', hide=True).stdout.strip()
    if device_short_sn is None:
        raise ValueError("Both device_new_name and device_short_sn must be provided")

def set_hostname(c):
    c.run(f'hostnamectl set-hostname {args.device_new_name}-{device_short_sn}')

def save_hostname(c):
    c.run(f'echo $(hostname) > /mnt/data/etc/vestasync/hostname')

def restore_hostname(c):
    c.run(f'hostnamectl set-hostname $(cat /mnt/data/etc/vestasync/hostname)')


def prepare_packages_wb(c):
    c.run('apt update')
    c.run('apt install git apt-transport-https ca-certificates htop sudo mc wget curl jq zip gzip tar  -y')
    c.run('apt-get -y autoremove')
    c.run('apt-get -y clean')
    c.run('apt-get -y autoclean ')


def configure_git(c):
    c.run(f'git config --global user.name vestasync_wb_$(hostname)_manual')
    c.run(f'git config --global user.email "vestasync@fake.mail"')
    c.run(f'git config --global init.defaultBranch "master"')

def create_repo(c):
    hostname = c.run('hostname', hide=True).stdout.strip()
    headers = {'Authorization': f'token {args.gitea_token}', 'Content-Type': 'application/json'}
    data = {"name": hostname, "private": False}
    response = requests.post(f'{args.vestasync_gitea_protocol}://{args.vestasync_gitea_host}:{args.vestasync_gitea_port}/api/v1/user/repos', headers=headers, json=data)
    if response.status_code == 201:  # 201 - Created, ожидаемый код успешного создания репозитория
        print("Repository created successfully.")
    elif response.status_code == 409:  # 409 - Conflict, репозиторий уже существует
        print("Error: Repository already exists.")
        print("Exiting...")
        sys.exit(1)
    else:
        print(f"Error: Unexpected HTTP status code {response.status_code}")
        print("Exiting...")
        sys.exit(1)


def init_repo(c):
    hostname = c.run('hostname', hide=True).stdout.strip()
    c.run('cd /mnt/data/etc/ && git init')
    c.run(f'cd /mnt/data/etc/ && git remote add origin {args.vestasync_gitea_protocol}://{gitea_user}:{args.gitea_token}@{args.vestasync_gitea_host}:{args.vestasync_gitea_port}/{gitea_user}/{hostname}.git')


def copy_wb_rule(c):
    c.put("./files/vestasync.js", "/mnt/data/etc/wb-rules/vestasync.js")

def create_automac_systemd(c):
    apply_macs_script_path = "/usr/local/bin/apply_macs.sh"
    c.put("./files/apply_macs.sh", apply_macs_script_path)
    c.run(f"chmod +x {apply_macs_script_path}")

    c.put("./files/apply_macs.service", "/etc/systemd/system/apply_macs.service")
    c.run("systemctl daemon-reload")
    c.run("systemctl enable apply_macs.service")

def create_autogit_systemd(c):
    pushgit_script_path = "/usr/local/bin/pushgit.sh"
    c.put("./files/pushgit.sh", pushgit_script_path)
    c.run(f"chmod +x {pushgit_script_path}")

    pushgit_inotify_script_path = "/usr/local/bin/pushgit_inotify.sh"
    c.put("./files/pushgit.sh", pushgit_inotify_script_path)
    c.run(f"chmod +x {pushgit_inotify_script_path}")

    c.put("./files/pushgit.service", "/etc/systemd/system/pushgit.service")
    c.put("./files/pushgit.timer", "/etc/systemd/system/pushgit.timer")

    c.put("./files/pushgit_inotify.service", "/etc/systemd/system/pushgit_inotify.service")

    c.run("systemctl daemon-reload")
    c.run("systemctl enable pushgit.timer")
    c.run("systemctl start pushgit.timer")
    c.run("systemctl enable pushgit_inotify.service")
    c.run("systemctl start pushgit_inotify.service")

def reboot(c):
    c.run("reboot > /dev/null 2>&1 || true")

def git_clone(c):
    c.run(f'mkdir /mnt/data/{args.source_hostname}_etc ', hide=True)
    c.run(f'git clone {args.vestasync_gitea_protocol}://{gitea_user}:{args.gitea_token}@{args.vestasync_gitea_host}:{args.vestasync_gitea_port}/{gitea_user}/{args.source_hostname}.git /mnt/data/{args.source_hostname}_etc')

def copy_etc(c):
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    archive_name = f"backup_{current_date}.tar.gz"
    print(f"Remove old .git...")
    c.run(f"rm -rf /mnt/data/etc/.git")
    print(f"Create backup: /mnt/data/{archive_name}")
    c.run(f"tar -czvf /mnt/data/{archive_name} -C /mnt/data etc", hide=True)

    files_and_folders = c.run("find /mnt/data/WB2-A3TBJXLS_etc", hide=True).stdout.strip().split('\n')
    files_and_folders = [item for item in files_and_folders if ".git" not in item]

    for item in files_and_folders:
        dest_item = item.replace(f"/{args.source_hostname}_etc/", "/etc/")
        if c.run(f"test -f {item}", hide=True, warn=True).ok:
            c.run(f"cat {item} > {dest_item}")
        elif c.run(f"test -d {item}", hide=True, warn=True).ok:
            c.run(f"mkdir -p {dest_item}")
        print(f"Restore: {item} -> {dest_item}")

    print(f"Сopy source .git...")
    c.run(f"cp -R /mnt/data/{args.source_hostname}_etc/.git /mnt/data/etc/.git")

    print(f"Remove source etc...")
    c.run(f"rm -rf /mnt/data/{args.source_hostname}_etc")

    print(f"Restore completed")

def ppush_the_repo(c):
    c.run('cd /mnt/data/etc/ && git add .', hide=True)
    try:
        c.run('cd /mnt/data/etc/ && git commit -m "$(date)"', hide=True)
    except UnexpectedExit as e:
        if 'nothing to commit' in e.result.stdout:
            print("Nothing to commit, exit")
        else:
            print(f"Error: {e.result.stderr}")
    c.run('cd /mnt/data/etc/ && git push -u origin master', hide=True)

def run_user_cmd(c):
    user_cmd_file = "/tmp/user_cmd.sh"
    c.put("user_cmd.sh", user_cmd_file)
    c.run(f"chmod +x {user_cmd_file}")
    c.run(f"{user_cmd_file}")
    c.run(f"rm {user_cmd_file}")

def save_mac_in_cfg(c):
    hostname = c.run('hostname', hide=True).stdout.strip()
    interfaces_info = c.run("ip -j a", hide=True).stdout.strip()
    interfaces_data = json.loads(interfaces_info)
    c.run("mkdir -p /mnt/data/etc/vestasync/macs")
    for interface in interfaces_data:
        ifname = interface["ifname"]
        if re.match(r'^(eth|wlan)', ifname):
            mac_address = interface["address"]
            c.run(f"echo {mac_address} > /mnt/data/etc/vestasync/macs/{ifname}")



def device_install():
    with Connection(host=args.device_ip, user=device_user, connect_kwargs={"password": "wirenboard"}) as c:
        prepare_packages_wb(c)
        configure_git(c)
        get_short_sn(c)
        set_hostname(c)
        create_repo(c)
        init_repo(c)
        ppush_the_repo(c)
        save_mac_in_cfg(c)
        save_hostname(c)
        copy_wb_rule(c)
        ppush_the_repo(c)
        create_automac_systemd(c)
        create_autogit_systemd(c)
        run_user_cmd(c)
        reboot(c)

def device_restore():
    with Connection(host=args.device_ip, user=device_user) as c:
        #prepare_packages_wb(c)
        #configure_git(c)
        #git_clone(c)
        #copy_etc(c)
        #restore_hostname(c)
        #ppush_the_repo(c)

        create_autogit_systemd(c)
        create_automac_systemd(c)


if __name__ == '__main__':
    try:
        args.vestasync_gitea_protocol, args.vestasync_gitea_host, args.vestasync_gitea_port = parse_address(args.gitea_address)
        del args.gitea_address
    except ValueError as e:
        print(e)
        exit(1)

    if cmd_args.cmd == "install":
        device_install()
    if cmd_args.cmd == "restore":
        device_restore()







