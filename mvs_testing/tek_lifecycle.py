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

DEBUG = False
PUBLISH_DEBUG = False

envs = ["staging", "test", "prod", "staging-e2e"]
admin_base_url = ""
base_url = ""
admin_key = ""
device_key = ""
health_authority_id = ""
key_server = ""

endpoints = {
    "issue": "/api/issue",
    "batch_issue": "/api/batch-issue",
    "verify": "/api/verify",
    "certificate": "/api/certificate"
}
headers = {
    "Content-Type": "application/json",
    "accept": "application/json",
    "x-api-key": device_key
}

def get_env_details(env):
    global admin_base_url
    global base_url
    global admin_key
    global device_key
    global health_authority_id
    global key_server
    with open("api.json") as f:
        data = json.load(f)
        admin_base_url = data[env]["admin_base_url"]
        base_url = data[env]["base_url"]
        admin_key = data[env]["admin_key"]
        device_key = data[env]["device_key"]
        health_authority_id = data[env]["health_authority_id"]
        key_server = data[env]["key_server"]

def issue_code(symptom_test_date):
    url = admin_base_url + endpoints["issue"]
    headers["x-api-key"] = admin_key
    payload = {
        "symptomDate": symptom_test_date,
        "testDate": symptom_test_date,
        "testType": "confirmed",
        "tzOffset": 0,
        "padding": base64.b64encode(os.urandom(16)).decode("utf-8")
    }
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res_dict = json.loads(res.content.decode("utf-8"))
    if DEBUG:
        print(json.dumps(res_dict, indent=4))
    return res_dict["code"]

def bulk_issue_code(num_codes, symptom_test_date):
    url = admin_base_url + endpoints["batch_issue"]
    headers["x-api-key"] = admin_key
    payload = {
        "codes": [],
        "padding": base64.b64encode(os.urandom(16)).decode("utf-8")
    }
    code_payload = {
        "symptomDate": symptom_test_date,
        "testDate": symptom_test_date,
        "testType": "confirmed",
        "tzOffset": 0,
        "padding": base64.b64encode(os.urandom(16)).decode("utf-8")
    }
    for x in range(num_codes):
        payload["codes"].append(code_payload)
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res_dict = json.loads(res.content.decode("utf-8"))
    if DEBUG:
        print(json.dumps(res_dict, indent=4))
    return res_dict["codes"]

def verify_code(code):
    url = base_url + endpoints["verify"]
    headers["x-api-key"] = device_key
    payload = {
        "code": code,
        "accept": ["confirmed"],
        "padding": base64.b64encode(os.urandom(16)).decode("utf-8")
    }
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res_dict = json.loads(res.content.decode("utf-8"))
    if DEBUG:
        print(json.dumps(res_dict, indent=4))
    return res_dict["token"]

def get_certificate(token, ekeyhmac):
    url = base_url + endpoints["certificate"]
    headers["x-api-key"] = device_key
    payload = {
        "token": token,
        "ekeyhmac": ekeyhmac,
        "padding": base64.b64encode(os.urandom(16)).decode("utf-8")
    }
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res_dict = json.loads(res.content.decode("utf-8"))
    if DEBUG:
        print(json.dumps(res_dict, indent=4))
    return res_dict["certificate"]

def publish_keys(keys, certificate, secret):
    headers["x-api-key"] = None
    url = key_server
    payload = {
        "temporaryExposureKeys": keys,
	    "healthAuthorityID": health_authority_id,
	    "verificationPayload": certificate,
	    "hmacKey": secret,
	    "padding": base64.b64encode(os.urandom(16)).decode("utf-8"),
    }
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res_dict = json.loads(res.content.decode("utf-8"))
    if PUBLISH_DEBUG:
        print("URL: " + acol.GRN + url + acol.END)
        print(json.dumps(res_dict, indent=4))
        print("Response code: " + acol.GRN + str(res.status_code) + acol.END)
    print("=====")
    print("Using healthAuthorityID: " + acol.YEL + payload["healthAuthorityID"] + acol.END)
    try:
        print("insertedExposures: " + acol.GRN + str(res_dict["insertedExposures"]) + acol.END)
    except Exception as e:
        print(acol.FAIL + "PUBLISH FAILED!" + acol.END)
        exit(1)

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
        if n < 3:
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

def select_env():
    menu = {}
    print("Select environment:")
    for n,e in enumerate(envs):
        menu[str(n)] = e
    for key in sorted(menu.keys()):
        print(" " + str(int(key)+1) + ": " + menu[key])
    ans = str(int(input("\n > ")) - 1)
    return menu[ans]

def main():
    print(acol.HDR + " === TEK Verification and Publish Tool === " + acol.END)

    env = select_env()
    get_env_details(env)
    print("---------------------------------")
    print("Selected environment: "+acol.YEL+ env +acol.END)
    print("---------------------------------")

    input("\n >>> Press "+acol.BLD+"ENTER"+acol.END+" to "+acol.BLD+"generate keys"+acol.END+".")
    print("Generating keys...")
    num_keys = random.randint(12, 15)
    keys = gen_keys(num_keys)
    print("Number of keys generated: "+acol.CYN+"{}".format(num_keys)+acol.END+" (showing first 3)")

    input("\n >>> Press "+acol.BLD+"ENTER"+acol.END+" to "+acol.BLD+"BULK issue codes"+acol.END+".")
    print("BULK issuing code...")
    num_codes = random.randint(3, 8)
    codes = bulk_issue_code(num_codes, datetime.datetime.now().strftime("%Y-%m-%d"))
    for code in codes:
        print("batch code: " + acol.YEL + code["code"] + acol.END)

    input("\n >>> Press "+acol.BLD+"ENTER"+acol.END+" to "+acol.BLD+"issue a SINGLE code"+acol.END+".")
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
