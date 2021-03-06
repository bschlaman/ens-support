#!/bin/bash
set -u

PROP_FILE=urls.properties
NKS=V1_PROD_API
INDEX=VA_INDEX_FILE
ROOT=VA_EXPORT_ROOT

########### Setting the vars
STATE_INDEX_FILE=$(grep $INDEX $PROP_FILE | grep -v \# | cut -d= -f2)
STATE_EXPORT_ROOT=$(grep $ROOT $PROP_FILE | cut -d= -f2)
NKS_API=$(grep $NKS $PROP_FILE | cut -d= -f2)
###########

# Run this script from inside export-analyzer, make sure WORKING_DIR is created and empty
# Put the one you want on the bottom :)
WORKING_DIR=AZ_export_analyzer
WORKING_DIR=AL_export_analyzer
WORKING_DIR=VA_export_analyzer

# Probably some go-ish way to check this, but whatever
[ $(basename $PWD) != "export-analyzer" ] && echo Error: need to be inside export-analyzer tool && exit 1
[ ! -d $WORKING_DIR ] && echo Error: $WORKING_DIR not found... && exit 1
[ "$(ls -A $WORKING_DIR)" ] && echo Error: $WORKING_DIR not empty... && exit 1

function prep_env(){
	mkdir -v state_zips nks_zips state_json nks_json
	#touch state_keys nks_keys matching_keys missing_keys
	echo -n "" > state_keys
	echo -n "" > nks_keys
	echo -n "" > matching_keys
	echo -n "" > missing_keys
}

function dl_state_exports(){
	echo Getting STATE exports...
	EXPORTS=$(curl -s $STATE_INDEX_FILE | sed 's/\r$//')
	pushd state_zips > /dev/null 2>&1
	for ex in $EXPORTS ; do
		echo "##[STATE] Downloading: " $ex
		curl -sO $STATE_EXPORT_ROOT/$ex
	done
	popd > /dev/null 2>&1
}

function dl_nks_exports(){
	echo Getting NKS exports...
	EXPORTS=$(curl -s $NKS_API/index.txt | sed 's/^.*\///')
	pushd nks_zips > /dev/null 2>&1
	for ex in $EXPORTS ; do
		echo "##[NKS] Downloading: " $ex
		curl -sO $NKS_API/$ex
	done
	popd > /dev/null 2>&1
}

function analyze_state_exports(){
	pushd state_json > /dev/null 2>&1
	echo "[STATE] Analyzing all state exports..."
	go run github.com/google/exposure-notifications-server/tools/export-analyzer -tek-age=672h0m0s --file=../state_zips/* > state_output.json 2>&1
	popd > /dev/null 2>&1
}

function analyze_nks_exports(){
	pushd nks_json > /dev/null 2>&1
	echo "[NKS] Analyzing all NKS exports..."
	go run github.com/google/exposure-notifications-server/tools/export-analyzer -tek-age=672h0m0s --file=../nks_zips/* > nks_output.json 2>&1
	popd > /dev/null 2>&1
}

function extract_keys(){
	echo "Extracting state keys..."
	grep \"key_data\": state_json/* | cut -d'"' -f4 > state_keys
	sort -o state_keys state_keys
	echo "Extracting nks keys..."
	grep \"key_data\": nks_json/* | cut -d'"' -f4 > nks_keys
	sort -o nks_keys nks_keys
	echo -e "Total number of state keys: ${BLD}${YEL}$(wc -l < state_keys)${NC}"
}

function key_search(){
	comm -12 state_keys nks_keys > matching_keys
	comm -23 state_keys nks_keys > missing_keys
	echo -e "Total matching keys: ${BLD}${GRN}$(wc -l < matching_keys)${NC}"
	echo -e "Total missing keys: ${BLD}${RED}$(wc -l < missing_keys)${NC}"
}

function main(){
	echo -e "${BLD}${YEL}NOTE: YOU MUST RUN THIS SCRIPT USING export-analyzer v0.17.0 OR HIGHER!${NC}"
	echo " ### Running func prep_env ### "
	prep_env
	echo " ### Running func dl_state_exports ### "
	dl_state_exports
	echo " ### Running func dl_nks_exports ### "
	dl_nks_exports
	echo " ### Running func analyze_state_exports ### "
	analyze_state_exports
	echo " ### Running func analyze_nks_exports ### "
	analyze_nks_exports
	echo " ### Running func extract_keys ### "
	echo -e "\n${BLD}Extracting and analyzing keys...${NC}"
	extract_keys
	echo " ### Running func key_search ### "
	echo -e "\n${BLD}Comparing state keys with NKS keys...${NC}"
	key_search
}

RED='\033[0;31m';YEL='\033[0;33m';GRN='\033[0;32m';BLU='\033[0;96m';BLD='\033[0;1m';NC='\033[0;0;39m'
echo "Switching to $WORKING_DIR..."
pushd $WORKING_DIR > /dev/null 2>&1
main
popd > /dev/null 2>&1

