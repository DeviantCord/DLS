from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import binascii


keyPair = RSA.generate(3072)

pubKey = keyPair.publickey()
print(f"Public key:  (n={hex(pubKey.n)}, e={hex(pubKey.e)})")
pubKeyPEM = pubKey.exportKey()
print(pubKeyPEM.decode('ascii'))

print(f"Private key: (n={hex(pubKey.n)}, d={hex(keyPair.d)})")
privKeyPEM = keyPair.exportKey()
print(privKeyPEM.decode('ascii'))

with open("private.key", "w+") as privateKey:
    print("Writing private key")
    privateKey.write(privKeyPEM.decode('ascii'))
    privateKey.close()
with open("public.key", "w+") as publicKey:
    print("Writing public key")
    publicKey.write(pubKeyPEM.decode('ascii'))
    publicKey.close()

