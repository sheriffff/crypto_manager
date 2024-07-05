import yaml
import math
import urllib.parse
import hashlib
import hmac
import base64


def load_keys():
    with open("../keys.yaml", "r") as keys_file:
        keys = yaml.safe_load(keys_file)

    key = keys["APIKEY"]
    secret = keys["PRIVATEKEY"]
    return key, secret


def get_kraken_signature(urlpath, data, secret):
    postdata = urllib.parse.urlencode(data)
    encoded = (str(data['nonce']) + postdata).encode()
    message = urlpath.encode() + hashlib.sha256(encoded).digest()

    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    sigdigest = base64.b64encode(mac.digest())

    return sigdigest.decode()


def round_sig(x, sig=4):
    return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)


def round_sig_dict(d, sig=4):
    return {k: round_sig(v, sig) for k, v in d.items()}


def round_dict(d, n=0):
    if n == 0:
        return {k: round(v) for k, v in d.items()}
    else:
        return {k: round(v, n) for k, v in d.items()}
