import hashlib
import random
import base64
import json
import requests
import os
import hmac

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    GRN = '\033[92m'
    YEL = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

env = "staging"
health_authority_id = "gov.pwcstage.exposurenotifications"
key_server = "https://dev.exposurenotification.health/v1/publish"
admin_base_url = ""
base_url = ""
admin_key = ""
device_key = ""

with open("api.json") as f:
    data = json.load(f)
    admin_base_url = data[env]["admin_base_url"]
    base_url = data[env]["base_url"]
    admin_key = data[env]["admin_key"]
    device_key = data[env]["device_key"]

endpoints = {
    "issue": "/api/issue",
    "verify": "/api/verify",
    "certificate": "/api/certificate"
}
headers = {
    "Content-Type": "application/json",
    "accept": "application/json",
    "x-api-key": device_key
}

def issue_code():
    url = admin_base_url + endpoints["issue"]
    headers["x-api-key"] = admin_key
    payload = {
        "symptomDate": "2020-12-01",
        "testDate": "2020-12-01",
        "testType": "confirmed",
        "tzOffset": 0,
        "padding": "asdfasdf"
    }
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res_dict = json.loads(res.content.decode("utf-8"))
    print("Issued code: {}".format(res_dict["code"]))
    return res_dict["code"]
    #print(json.dumps(res_dict, indent=4))

def verify_code(code):
    url = base_url + endpoints["verify"]
    headers["x-api-key"] = device_key
    payload = {
        "code": code,
        "accept": ["confirmed"],
        "padding": "asdfasdf"
    }
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res_dict = json.loads(res.content.decode("utf-8"))
    return res_dict["token"]
    #print(json.dumps(res_dict, indent=4))

def get_certificate(token, ekeyhmac):
    url = base_url + endpoints["certificate"]
    headers["x-api-key"] = device_key
    payload = {
        "token": token,
        "ekeyhmac": ekeyhmac,
        "padding": "Zm9vCg=="
    }
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res_dict = json.loads(res.content.decode("utf-8"))
    return res_dict["certificate"]
    #print(json.dumps(res_dict, indent=4))

def publish_keys(keys, certificate, secret):
    headers["x-api-key"] = None
    url = key_server
    payload = {
        "temporaryExposureKeys": keys,
	    "healthAuthorityID": health_authority_id,
	    "verificationPayload": certificate,
	    "hmacKey": secret,
	    "padding": "foo"
    }
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res_dict = json.loads(res.content.decode("utf-8"))
    print(json.dumps(res_dict, indent=4))

def gen_keys(n):
    keys = []
    for x in range(n):
        tek = {
            "key": base64.b64encode(os.urandom(16)).decode("utf-8"),
            "rollingStartNumber": 2678110 - x*144,
            "rollingPeriod": 144,
            "transmissionRisk": random.randint(1,5)
        }
        keys.append(tek)
    for n,x in enumerate(keys):
        print(bcolors.OKCYAN + "key {}:".format(n) + bcolors.ENDC + "\n{}".format(json.dumps(keys[n], indent=2)))
    return keys

def mutate_keys(keys):
    keys = sorted(keys, key = lambda i: i["key"])
    keys_str = ""
    for key in keys:
        keys_str += "{}.{}.{}.{},".format(key["key"], key["rollingStartNumber"], key["rollingPeriod"], key["transmissionRisk"])
    return keys_str[:-1]

def gen_hmac(secret, message):
    h = hmac.new(secret, message.encode("utf-8"), hashlib.sha256)
    b = base64.b64encode(h.digest())
    return str(b, "utf-8")

def main():
    print(bcolors.HEADER + " === TEK Verification and Publish Tool === " + bcolors.ENDC)

    input("\n >>> Press ENTER to generate keys.")
    print("Generating keys...")
    keys = gen_keys(40)

    input("\n >>> Press ENTER to issue a code.")
    print("Issuing code...")
    code = issue_code()
    print("code: " + bcolors.YEL + code + bcolors.ENDC)
    print("This code will expire in 15 min.")

    input("\n >>> Press ENTER to verify the code")
    print("Exchanging the code for a long-term token...")
    token = verify_code(code)
    print("long-term token: " + bcolors.YEL + token[0:19] + "..." + bcolors.ENDC)

    input("\n >>> Press ENTER to calculate the HMAC of your keys")
    secret = bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    secret_str = str(base64.b64encode(secret), "utf-8")
    print("Converting keys into a string...")
    message = mutate_keys(keys)
    print("key string: " + bcolors.YEL + message + bcolors.ENDC)
    print("Generating HMAC of keys...")
    print("Using secret: " + bcolors.GRN + secret_str + bcolors.ENDC)
    ekeyhmac = gen_hmac(secret, message)
    print("hmac: " + bcolors.OKCYAN + ekeyhmac + bcolors.ENDC)

    input("\n >>> Press ENTER to get verification certificate.")
    certificate = get_certificate(token, ekeyhmac)
    print("certificate: " + bcolors.YEL + certificate[0:19] + "..." + bcolors.ENDC)

    input("\n >>> Press ENTER to publish keys.")
    #print(certificate)
    publish_keys(keys, certificate, secret_str)
    # menu = {"1":("issue",issue_code),
    #         "2":("verify",verify_code),
    #         "3":("certificate",get_certificate)
    #    }
    # for key in sorted(menu.keys()):
    #      print(key+":" + menu[key][0])

    # ans = input("Make A Choice")
    # menu.get(ans,[None,exit(1)])[1]()

if __name__ == "__main__":
    main()
