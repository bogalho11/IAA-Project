from flask import Flask, request
import requests, random, string

from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
import base64

app = Flask(__name__)

challenges = []

@app.route("/auth_req", methods=["POST"])
def auth_req():
    user_data = request.get_json()
    r = requests.get("http://127.0.0.1:3173/resolve_did", json={"did_identifier": user_data["did_identifier"], "loa": user_data["loa"]})

    public_key = r.json()["public_key"]
    challenge = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(64))
    challenges.append((user_data["did_identifier"], challenge, public_key))

    return {"challenge": challenge}

@app.route("/validate_challenge", methods=["POST"]) 
def validate_challenge():
    signature = bytes(request.get_json()["signature"])
    did_identifier = request.get_json()["did_identifier"]

    for challenge in challenges:
        if did_identifier == challenge[0]:
            original_chall = challenge[1]
            holder_pub_key = challenge[2]

    holder_pub_key = load_pem_public_key(holder_pub_key.encode("utf-8"))

    #Hash of the challenge
    digest = hashes.Hash(hashes.SHA256())
    digest.update(original_chall.encode('utf-8'))
    hashed_challenge = digest.finalize()

    print(hashed_challenge)

    # check the attribute signature
    try:
        holder_pub_key.verify(
            signature,
            hashed_challenge,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            Prehashed(hashes.SHA256())
        )

        print(f"Signature is valid.")
        return {"valid": "yes"}      
    except Exception as inst:
        print(inst)
        print(f"Signature is invalid.")
        return {"valid": "no"}     

if __name__ == '__main__':
    app.run(debug=True, port=3317)
