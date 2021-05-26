#!/bin/bash

NKS_URL=$(grep NKS_DEV ./urls.properties | cut -d"=" -f2)
OUTPUT_FILE=res.log

num=10000
for x in $(seq 0 $num) ; do
	echo -n "$x" "[ $(date '+%Y-%m-%d %H:%M:%S') ]"
	curl -sS -X POST -d @padding.json -H "X-Chaff: foo" $NKS_URL
	echo
	sleep 0.5
done >> $OUTPUT_FILE 2>&1
