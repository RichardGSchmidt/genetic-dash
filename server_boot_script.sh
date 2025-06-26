#!/bin/bash
# This script updates and rebuilds a container hosted on an Ubuntu server
# on execution.  Used with chrontab for rebuild on server reboot.


# To implement, make a copy and change the path to the location you cloned the repo
# chmod 555 the script
# Then add a chrontab via chrontab -e for the following:
# @reboot /path/to/script/server_boot_script.sh

#crontab doesn't provide path in it's environment
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

#go to path if exists or exit, you need to manually put the correct directory.
#!/bin/bash

APP_DIR="/home/$USER/genetic-dash"
cd "$APP_DIR" || exit 1

echo "📥 Checking for updates..."

# Fetch latest remote changes
git fetch origin master

# Check if there are new commits
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/master)

if [ "$LOCAL_HASH" != "$REMOTE_HASH" ]; then
    echo "🔄 Changes detected, pulling and rebuilding..."

    git pull origin master || exit 1
    docker build -t genetic-dash . || exit 1

    docker stop genetic-dash-container 2>/dev/null
    docker rm genetic-dash-container 2>/dev/null

    docker run -d --name genetic-dash-container -p 8050:8050 genetic-dash || exit 1

    echo "✅ Updated successfully!"
else
    echo "✅ No changes — skipping rebuild."
fi