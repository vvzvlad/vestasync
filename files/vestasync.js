defineVirtualDevice("vestasync", {
    title: "Vestasync",
    cells: {
        "Last push": {
            type: "text",
            value: "Update...",
            title: "Last push"
        },
        "Current commit": {
            type: "text",
            value: "Update...",
            title: "Last commit hash"
        },
        autopush: {
            type: "switch",
            value: true,
            title: "Auto push on files changed"
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
                dev.vestasync["Last push"] = human_readable_time;
            }
        }
    });
    runShellCommand("git -C /mnt/data/etc log -1 --format=%H", {
        captureOutput: true,
        exitCallback: function (exitCode, capturedOutput) {
            if (exitCode === 0) {
                var shortenedCommit = capturedOutput.trim().substring(0, 10);
                dev.vestasync["Current commit"] = shortenedCommit;
            }
        }
    });

    runShellCommand("systemctl is-active pushgit_inotify.service", {
        captureOutput: true,
        exitCallback: function (exitCode, capturedOutput) {
            var isEnabled = capturedOutput.trim() === "active";
            dev.vestasync.autopush = isEnabled;
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


defineRule("_vestasync_autopush", {
    whenChanged: "vestasync/autopush",
    then: function (newValue, devName, cellName) {
        if (dev.vestasync.autopush) {
            runShellCommand("systemctl daemon-reload ; systemctl enable pushgit_inotify.service ; systemctl start pushgit_inotify.service");
        } else {
            runShellCommand("systemctl stop pushgit_inotify.service ; systemctl disable pushgit_inotify.service");
        }
    }
});


_update_vestasync();
setInterval(_update_vestasync, 11000);


