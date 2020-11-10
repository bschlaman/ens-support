#!/bin/bash
set -u

# NKS
V1_INTEGRATION_API=https://encdn.integration.exposurenotification.health/v1h1
#V1_PROD_API=https://encdn.prod.exposurenotification.health/
#V1_DEV_API=https://encdn.dev.exposurenotification.health/

# STATES
#VA_PROD_API=https://storage.googleapis.com/prod-export-key/exposureKeyExport-US/index.txt
AZ_INDEX_FILE=https://exposure.wehealth.org/US-AZ/index.txt
AZ_EXPORT_ROOT=https://exposure.wehealth.org
VA_UAT_INDEX_FILE=https://storage.googleapis.com/exposure-keys-uat-sync/exposureKeyExport-US/index.txt
VA_UAT_EXPORT_ROOT=https://storage.googleapis.com/exposure-keys-uat-sync
VA_INDEX_FILE=https://storage.googleapis.com/prod-export-key/exposureKeyExport-US/index.txt
VA_EXPORT_ROOT=https://storage.googleapis.com/prod-export-key
AL_INDEX_FILE=https://covidexposurestorage.z13.web.core.windows.net/nationalIndex.txt
AL_EXPORT_ROOT=https://covidexposurestorage.z13.web.core.windows.net

########### Setting the vars
STATE_INDEX_FILE=$VA_INDEX_FILE
STATE_EXPORT_ROOT=$VA_EXPORT_ROOT
NKS_API=$V1_INTEGRATION_API
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
  for zip in ../state_zips/* ; do
  	echo "[STATE] Analyzing: $(basename $zip)"
  	go run github.com/google/exposure-notifications-server/tools/export-analyzer --file=$zip > $(basename $zip).json 2>&1
  done
	popd > /dev/null 2>&1
}

function analyze_nks_exports(){
	pushd nks_json > /dev/null 2>&1
  for zip in ../nks_zips/* ; do
  	echo "[NKS] Analyzing: $(basename $zip)"
  	go run github.com/google/exposure-notifications-server/tools/export-analyzer --file=$zip > $(basename $zip).json 2>&1
  done
	popd > /dev/null 2>&1
}

function extract_keys(){
	echo "Extracting state keys..."
	grep \"key_data\": state_json/* | cut -d'"' -f4 > state_keys
	sort -o state_keys state_keys
	echo "Extracting nks keys..."
	grep \"key_data\": nks_json/* | cut -d'"' -f4 > nks_keys
	sort -o nks_keys nks_keys
	echo Total number of state keys: $(wc -l state_keys)
}

function key_search(){
	comm -12 state_keys nks_keys > matching_keys
	comm -23 state_keys nks_keys > missing_keys
	echo "Total matching keys: $(wc -l matching_keys)"
	echo "Total missing keys: $(wc -l missing_keys)"
}

function main(){
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
	extract_keys
	echo " ### Running func key_search ### "
	key_search
}

echo "Switching to $WORKING_DIR..."
pushd $WORKING_DIR > /dev/null 2>&1
main
popd > /dev/null 2>&1

