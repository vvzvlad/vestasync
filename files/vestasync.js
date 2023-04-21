defineVirtualDevice("vestasync", {
    title: "Vestasync",
    cells: {
        last_push: {
            type: "text",
            value: "Update...",
            title: "Last push"
        },
        last_commit: {
            type: "text",
            value: "Update...",
            title: "Last commit hash"
        },
        autopush_inotify: {
            type: "switch",
            value: false,
            title: "Auto push on files changed"
        },
        push_now: {
            type: "pushbutton",
            value: false,
            title: "Commit and push now"
        },
        hostname: {
            type: "text",
            value: "",
            title: "Hostname"
        }
    }
});


function _update_vestasync() {
    runShellCommand("git -C /mnt/data/etc log -1 --format=%ct", {
        captureOutput: true,
        exitCallback: function (exitCode, capturedOutput) {
            if (exitCode === 0) {
                var last_push_time = parseInt(capturedOutput);
                var now = new Date();
                var diff_in_seconds = Math.floor((now.getTime() / 1000) - last_push_time);
                var diff_in_minutes = Math.floor(diff_in_seconds / 60);
                var diff_in_hours = Math.floor(diff_in_minutes / 60);
                var diff_in_days = Math.floor(diff_in_hours / 24);
                var human_readable_time = "";
                if (diff_in_days > 0) {
                    human_readable_time = diff_in_days + " days ago";
                } else if (diff_in_hours > 0) {
                    human_readable_time = diff_in_hours + " hours ago";
                } else if (diff_in_minutes > 0) {
                    human_readable_time = diff_in_minutes + " minutes ago";
                } else {
                    human_readable_time = "just now";
                }
                dev.vestasync.last_push = human_readable_time;
            }
        }
    });
    runShellCommand("git -C /mnt/data/etc log -1 --format=%H", {
        captureOutput: true,
        exitCallback: function (exitCode, capturedOutput) {
            if (exitCode === 0) {
                var shortenedCommit = capturedOutput.trim().substring(0, 10);
                dev.vestasync.last_commit = shortenedCommit;
            }
        }
    });

    runShellCommand("systemctl is-active pushgit_inotify_special.service", {
        captureOutput: true,
        exitCallback: function (exitCode, capturedOutput) {
            var isEnabled = capturedOutput.trim() === "active";
            getControl("vestasync/autopush_inotify").setValue({ value: isEnabled, notify: false })
        }
    });

    runShellCommand("hostname", {
        captureOutput: true,
        exitCallback: function (exitCode, capturedOutput) {
            if (exitCode === 0) {
                var hostname = capturedOutput.trim();
                dev.vestasync.hostname = hostname;
            } else {
                console.error("Error checking hostname:", capturedOutput.trim());
            }
        }
    });

};



defineRule("_vestasync_autopush_inotify", {
    whenChanged: "vestasync/autopush_inotify",
    then: function (newValue, devName, cellName) {
        if (dev.vestasync.autopush_inotify) {
            runShellCommand("systemctl start pushgit_inotify_special.service");
            _update_vestasync();
        } else {
            runShellCommand("systemctl stop pushgit_inotify_special.service");
            _update_vestasync();
        }
    }
});



defineRule("_vestasync_push", {
    whenChanged: "vestasync/push_now",
    then: function (newValue, devName, cellName) {
        if (dev.vestasync.push_now) {
            runShellCommand("/usr/local/bin/pushgit.sh");
        }
    }
});


_update_vestasync();
setInterval(_update_vestasync, 60000);


