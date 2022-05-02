from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from errite.dls.stringutils import removeByteString
import binascii

file = open('private.key', 'r')
external_key = file.read()
key = RSA.import_key(external_key)
print("Please enter your password")
password = bytes(input(),'ascii')
encryptor = PKCS1_OAEP.new(key)
encrypted = encryptor.encrypt(password)
print("Encrypted:", removeByteString(str(binascii.hexlify(encrypted))))
result = removeByteString(str(binascii.hexlify(encrypted)))
result_file = open('resultold.txt', 'w+')
result_file.write(result)
result_file.close()

