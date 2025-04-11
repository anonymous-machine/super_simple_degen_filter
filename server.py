import os
from io import BytesIO
from datetime import datetime, timedelta

import torch
import uvicorn
import ipaddress
import requests

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import CLIPProcessor, CLIPModel
from PIL import Image

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if torch.backends.mps.is_available() and torch.backends.mps.is_built():
    device = "mps" 
elif torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

## biggest model
#model_string = "laion/CLIP-ViT-g-14-laion2B-s12B-b42K"

## medium model
model_string = "openai/clip-vit-large-patch14"

## smallest model
#model_string = "openai/clip-vit-base-patch32"


model = CLIPModel.from_pretrained(model_string).to(device)
processor = CLIPProcessor.from_pretrained(model_string)

class RequestData(BaseModel):
    image_url: str
    listPass: list[str]
    listFail: list[str]

@app.post("/analyze")
async def analyze(data: RequestData):
    #print(f'data is {data}')
    try:
        #print("getting image")
        try:
            response = requests.get(data.image_url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).convert("RGBA")
        except requests.exceptions.RequestException as e:
            print(f"HTTP error: {e}")
        except UnidentifiedImageError:
            print("The URL did not return a valid image.")

        texts = data.listPass + data.listFail

        inputs = processor(text=texts, images=image, return_tensors="pt", padding=True).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            image_embeds = outputs.image_embeds
            text_embeds = outputs.text_embeds

        image_embeds /= image_embeds.norm(dim=-1, keepdim=True)
        text_embeds /= text_embeds.norm(dim=-1, keepdim=True)

        similarity = torch.matmul(image_embeds, text_embeds.T).squeeze(0)  # shape: (N,)
        best_match_idx = similarity.argmax().item()
        best_match_text = texts[best_match_idx]

        result = "pass" if best_match_text in data.listPass else "fail"
        return {"result": result}

    except Exception as e:
        return {"error": str(e)}

# certificate generator 
def generate_self_signed_cert(cert_file="cert.pem", key_file="key.pem"):
    if os.path.exists(cert_file) and os.path.exists(key_file):
        return cert_file, key_file

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"LocalState"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"LocalCity"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"MyOrg"),
        x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.utcnow())
        .not_valid_after(datetime.utcnow() + timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(u"127.0.0.1")]), critical=False)
        .sign(key, hashes.SHA256())
    )

    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    with open(key_file, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    return cert_file, key_file

if __name__ == "__main__":
    cert_path, key_path = generate_self_signed_cert()
    uvicorn.run("server:app", host="127.0.0.1", port=19081, ssl_certfile=cert_path, ssl_keyfile=key_path, reload=True)
    #uvicorn.run("server:app", host="127.0.0.1", port=19081, reload=True)
