import hashlib
import random
import base64
import json
import requests
import os
import hmac
from time import time
import datetime

class acol:
    HDR = '\033[95m'
    BLU = '\033[94m'
    CYN = '\033[96m'
    GRN = '\033[92m'
    YEL = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BLD = '\033[1m'
    UNDERLINE = '\033[4m'

env = "staging"
admin_base_url = ""
base_url = ""
admin_key = ""
device_key = ""
health_authority_id = ""
key_server = ""

with open("api.json") as f:
    data = json.load(f)
    admin_base_url = data[env]["admin_base_url"]
    base_url = data[env]["base_url"]
    admin_key = data[env]["admin_key"]
    device_key = data[env]["device_key"]
    health_authority_id = data[env]["health_authority_id"]
    key_server = data[env]["key_server"]

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

def issue_code(symptom_test_date):
    url = admin_base_url + endpoints["issue"]
    headers["x-api-key"] = admin_key
    payload = {
        "symptomDate": symptom_test_date,
        "testDate": symptom_test_date,
        "testType": "confirmed",
        "tzOffset": 0,
        "padding": "asdfasdf"
    }
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res_dict = json.loads(res.content.decode("utf-8"))
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
    print("=====")
    print(json.dumps(payload, indent=4))
    print("=====")
    print(json.dumps(res_dict, indent=4))

def gen_keys(n):
    keys = []
    rolling_start_interval = int((time() / 86400) * 144)
    print((acol.YEL + "Current unix time: {}" + acol.END).format(int(time())))
    print((acol.YEL + "Unix interval time: {}" + acol.END).format(rolling_start_interval))
    for x in range(n):
        tek = {
            "key": base64.b64encode(os.urandom(16)).decode("utf-8"),
            "rollingStartNumber": rolling_start_interval - x*144,
            "rollingPeriod": 144,
            "transmissionRisk": random.randint(1,5)
        }
        keys.append(tek)
    for n,x in enumerate(keys):
        print(acol.CYN + "key {}:".format(n) + acol.END + "\n{}".format(json.dumps(keys[n], indent=2)))
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
    print(acol.HDR + " === TEK Verification and Publish Tool === " + acol.END)

    input("\n >>> Press "+acol.BLD+"ENTER"+acol.END+" to "+acol.BLD+"generate keys"+acol.END+".")
    print("Generating keys...")
    num_keys = random.randint(2, 5)
    keys = gen_keys(num_keys)
    print("Number of keys generated: {}".format(num_keys))

    input("\n >>> Press "+acol.BLD+"ENTER"+acol.END+" to "+acol.BLD+"issue a code"+acol.END+".")
    print("Issuing code...")
    code = issue_code(datetime.datetime.now().strftime("%Y-%m-%d"))

    print("code: " + acol.YEL + code + acol.END)
    print("This code will expire in 15 min.")

    input("\n >>> Press "+acol.BLD+"ENTER"+acol.END+" to "+acol.BLD+"verify the code"+acol.END+".")
    print("Exchanging the code for a long-term token...")
    token = verify_code(code)
    print("long-term token: " + acol.YEL + token[0:19] + "..." + acol.END)

    input("\n >>> Press "+acol.BLD+"ENTER"+acol.END+" to "+acol.BLD+"calculate the HMAC"+acol.END+" of your keys.")
    secret = bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])
    secret_str = str(base64.b64encode(secret), "utf-8")
    print("Converting keys into a string...")
    message = mutate_keys(keys)
    print("key string: " + acol.YEL + message + acol.END)
    print("Generating HMAC of keys...")
    print("Using secret: " + acol.GRN + secret_str + acol.END)
    ekeyhmac = gen_hmac(secret, message)
    print("hmac: " + acol.CYN + ekeyhmac + acol.END)

    input("\n >>> Press "+acol.BLD+"ENTER"+acol.END+" to get your "+acol.BLD+"verification certificate"+acol.END+".")
    certificate = get_certificate(token, ekeyhmac)
    print("certificate: " + acol.YEL + certificate[0:19] + "..." + acol.END)

    input("\n >>> Press "+acol.BLD+"ENTER"+acol.END+" to "+acol.BLD+"publish your keys"+acol.END+".")
    publish_keys(keys, certificate, secret_str)

if __name__ == "__main__":
    main()
