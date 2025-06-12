#!/bin/bash

#go to path if exists or exit
cd ~/genetic-dash || exit

#pull from git hub
git pull origin main

#build the dockerfile
docker build -t genetic-dash .

#stop and remove the existing container
docker stop genetic-dash-container
docker rm genetic-dash-container

# Run the updated container
docker run -d --name genetic-dash-container -p 8050:8050 genetic-dash