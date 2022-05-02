from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from errite.dls.stringutils import removeByteString
import binascii

file = open('private.key', 'r')
external_key = file.read()
key = RSA.import_key(external_key)
msg = b'Jeffrey died'
encryptor = PKCS1_OAEP.new(key)
encrypted = encryptor.encrypt(msg)
print("Encrypted:", binascii.hexlify(encrypted))
test:str = binascii.hexlify(encrypted)

decryptor = PKCS1_OAEP.new(key)
decrypted = decryptor.decrypt(binascii.unhexlify(test))
print("Str: " + removeByteString(str(decrypted)))
print('Decrypted:', decrypted)


