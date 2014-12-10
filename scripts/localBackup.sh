#!/bin/bash
appname=handshake-app

# declare the appname at the top of the file
# input arguments are the kinds to backup in the local ds
# PRE: dev_appserver must be running for the local server

for kind_input in "$@"
do
    appcfg.py download_data --application=s~$appname --url=http://$appname.appspot.com/_ah/remote_api/ --filename=$kind_input.csv --kind=$kind_input
    appcfg.py upload_data --filename=$kind_input.csv --url=http://localhost:8080/_ah/remote_api/
    rm $kind_input.csv
done

