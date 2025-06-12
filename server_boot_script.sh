#!/bin/bash
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

#go to path if exists or exit, you need to manually put the correct directory.
cd /home/$USER/genetic-dash || exit

#pull from git hub
git pull origin master

#build the dockerfile
docker build -t genetic-dash .

#stop and remove the existing container
docker stop genetic-dash-container
docker rm genetic-dash-container

# Run the updated container
docker run -d --name genetic-dash-container -p 8050:8050 genetic-dash