#!/bin/bash

# inspired by 
# http://stackoverflow.com/questions/2924697/how-does-one-output-bold-text-in-bash
bold=$(tput bold)
normal=$(tput sgr0)

SELECTOR=$1

DATABASE_DEST=$2

HTML_DEST=$3

CLASSIFICATION=$4

DUMPS=()
if [ $# -lt 5 ]; then
	echo ${bold}run${normal} selector database html_destination human_classification [dump]...
else
	count=0
	for arg in "$@"
	do
		count=$((count+1))
		if [ $count -gt 4 ]; then
			DUMPS=(${DUMPS[@]} $arg)
		fi
	done
	echo "classification..."
	./classify.py $SELECTOR $DATABASE_DEST ${DUMPS[@]}
	if [ $CLASSIFICATION -ne "none"]; then
		echo "denote errors according to human classification..."
		./helper.py --denote_errors $CLASSIFICATION $DATABASE_DEST
	fi
	echo "create html output..."
	./plot_report.py $DATABASE_DEST $HTML_DEST
	echo "Done!"
fi
