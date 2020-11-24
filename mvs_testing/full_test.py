import random
import base64
import json
import requests
import os
import hmac

env = "staging"
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

#print(admin_base_url,base_url,admin_key,device_key)
#exit(0)

key1 = {
    "key": "xxxx9hdz2SlxZ8GEgqTYpA==",
    "rollingStartNumber": 2674944,
    "rollingPeriod": 144,
    "transmissionRisk": 3
}
key2 = {
    "key": "yyyyhLzfG4uzXneNimkPRQ==",
    "rollingStartNumber": 2674944,
    "rollingPeriod": 144,
    "transmissionRisk": 5
}

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
        "symptomDate": "2020-11-11",
        "testDate": "2020-11-11",
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
    print("Token: {}".format(res_dict["token"]))
    return res_dict["token"]
    #print(json.dumps(res_dict, indent=4))

def get_certificate(token):
    url = base_url + endpoints["certificate"]
    headers["x-api-key"] = device_key
    payload = {
        "token": token,
        "ekeyhmac": "wfhgTIVov7y91plU8dThbvJi/dWoiY3kqJN4QCsR5Tg=",
        "padding": "Zm9vCg=="
    }
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    res_dict = json.loads(res.content.decode("utf-8"))
    print("Certificate: {}".format(res_dict["certificate"]))
    return res_dict["certificate"]
    #print(json.dumps(res_dict, indent=4))

def gen_keys(n):
    keys = []
    for x in range(n):
        tek = {
            "key": base64.b64encode(os.urandom(16)).decode("utf-8"),
            "rollingStartNumber": 2674944,
            "rollingPeriod": 144,
            "transmissionRisk": random.randint(1,5)
        }
        keys.append(tek)
    for n,x in enumerate(keys):
        print("key {}:\n{}".format(n, json.dumps(keys[n])))

def gen_hmac():
    out = hmac.digest

def main():
    #gen_keys(random.randint(2,9))
    #gen_hmac()
    #exit(0)
    code = issue_code()
    token = verify_code(code)
    certificate = get_certificate(token)
    
if __name__ == "__main__":
    main()
