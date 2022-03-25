#!/bin/sh

echo $@ | grep 'y.example.net' > /dev/null && sleep 2
rsync $@
