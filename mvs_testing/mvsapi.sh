ADMIN_KEY=$(cat admin_api)
DEVICE_KEY=$(cat device_api)
ADMIN_BASE_URL=https://adminapi.encv-test.org
BASE_URL=https://apiserver.encv-test.org
ISSUE=/api/issue
VERIFY=/api/verify
CERTIFICATE=/api/certificate

#curl https://example.encv.org/api/method \
#  --header "content-type: application/json" \
#  --header "accept: application/json" \
#  --header "x-api-key: abcd.5.dkanddssk"

function issue(){
	BODY=issue_code.json
	curl -i $ADMIN_BASE_URL/$ISSUE \
		--header "content-type: application/json" \
		--header "accept: application/json" \
		--header "x-api-key: $ADMIN_KEY" \
		-d @./$BODY
}

function verify(){
	BODY=verify_code.json
	curl -i $BASE_URL/$VERIFY \
		--header "content-type: application/json" \
		--header "accept: application/json" \
		--header "x-api-key: $DEVICE_KEY" \
		-d @./$BODY
}

function certificate(){
	BODY=certificate.json
	curl -i $BASE_URL/$CERTIFICATE \
		--header "content-type: application/json" \
		--header "accept: application/json" \
		--header "x-api-key: $DEVICE_KEY" \
		-d @./$BODY
}

function publish(){
	BODY=publish.json
	curl -i https://dev.exposurenotification.health/v1/publish \
		-X "POST" \
		-H "content-type: application/json" \
		-H "accept: application/json" \
		-d @./$BODY
}

select action in issue verify certificate publish
do
$action
done
