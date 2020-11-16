import random
import base64
import json
import requests
import os

admin_key = "VkVkjO9lBCenNGAz7CtkvEkFb6AfUkPZWXYE9Dx6IciJf2DKEirmny4HkS_8ycprkB_T3JcOtPvy-5FwkpusSg.14.fsaFDcg9PqjkrO1kHyIRAmNFzGUfuWo1dg8StS1gR6Brlu7CxWUcDKP9NtYL3fhPRdQ7yRB9KCqbImzSbxGJ_w"
device_key = "YCkfoo6DIMCQS4lcFd3dAaXSfiqQ-MiT1uIvMn7r-KQ4FEWms9-IbqfnQUDwDh6LN6ehbsApGKfUEK31vLE3bQ.14.eoK9Qm1P_5zt7LwuLtzm6vrBeQ-yuRk7ZrmTx5qP8-_037XIHqgH1GWP-2GCcg0HVl3aSnshXyu0B-o0DweGTw"
admin_base_url = "https://adminapi.encv-test.org"
base_url = "https://apiserver.encv-test.org"
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
        "symptomDate": "2020-11-01",
        "testDate": "2020-11-01",
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
    exit(0)

def main():
    gen_keys(random.randint(2,9))
    code = issue_code()
    token = verify_code(code)
    certificate = get_certificate(token)
    
if __name__ == "__main__":
    main()
