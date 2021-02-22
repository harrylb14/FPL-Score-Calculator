#!/bin/bash
app="fpl_scores"
docker build -t ${app} .
docker run -d -p 10001:80 \
  --name=${app} \
  -v $PWD:/app ${app}