from Crypto.Cipher import AES
from Crypto import Random
from timeit import Timer, timeit, repeat
from pprint import pprint
from DiffieHellman import DiffieHellman

# repetitions for each test
rep = 100

# AES: 
# - 128 bits block size (16 Bytes)
# - 128, 192 and 256 bits key sizes. (16, 24, 32 Bytes)
BLOCK_SIZE = 16
KEY_SIZE = 32
mode = AES.MODE_CBC

# standardized padding TBD, e.g. PKCS#7 or PKCS#5
PADDING = '{'
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING

EncodeAES = lambda c, s: c.encrypt(pad(s))
DecodeAES = lambda c, e: c.decrypt(e).rstrip(PADDING)

## Encryption benchmarks
# generate a random secret key
key = Random.new().read(KEY_SIZE)
# generate a random IV
iv_bytes = Random.new().read(BLOCK_SIZE)
# create a cipher object using the random key and IV
cipher = AES.new(key, mode, iv_bytes)

# measure latency of encrypting one message 
# for various message lengths (N = number of characters)
etimes = []
for N in [1, 10, 100, 1000, 10000]:
    etimes.append(timeit("EncodeAES(cipher, 'c' * N)", 
                         setup="from __main__ import EncodeAES, cipher, N", number=rep) / rep)
    
# strange effect for N = 1
print 'times to encrypt N Bytes: '
pprint( dict(zip([1, 10, 100, 1000, 10000], etimes)) )

# measure latency of encrypting M messages of N characters each
# encryption of M messages is simply done by repeating M times
M = 1000 # messages
N = 100 # characters / Bytes
stmt = '''
for i in xrange(M):
    encoded = EncodeAES(cipher, 'c' * N)
'''
print 'time to encrypt ' + str(M) + ' messages, each of ' + str(N) + ' Bytes: ' , \
timeit(stmt, setup="from __main__ import EncodeAES, cipher, M, N", number=rep) / rep

## Decryption benchmarks
dtimes = []
for N in [1, 10, 100, 1000, 10000]:
    # generate a random secret key
    key = Random.new().read(KEY_SIZE)
    # generate a random IV
    iv_bytes = Random.new().read(BLOCK_SIZE)
    # create a cipher object using the random key and IV
    cipher = AES.new(key, mode, iv_bytes)
    # decode the encoded string
    encoded = EncodeAES(cipher, 'c' * N)
    dtimes.append(timeit("DecodeAES(cipher, iv_bytes + encoded)[len(iv_bytes):]", 
                         setup="from __main__ import DecodeAES, cipher, iv_bytes, encoded", number=rep) / rep)
    
# strange effect for N = 1
print 'times to decrypt N Bytes: '
pprint( dict(zip([1, 10, 100, 1000, 10000], dtimes)) )

# decrypting M times
M = 1000
N = 100
# generate a random secret key
key = Random.new().read(KEY_SIZE)
# generate a random IV
iv_bytes = Random.new().read(BLOCK_SIZE)
# create a cipher object using the random key and IV
cipher = AES.new(key, mode, iv_bytes)
# decode the encoded string
encoded = EncodeAES(cipher, 'c' * N)
stmt='''
for i in xrange(M):
    decoded = DecodeAES(cipher, iv_bytes + encoded)[len(iv_bytes):]
'''
print 'time to decrypt ' + str(M) + ' messages, each of ' + str(N) + ' Bytes of plaintext size: ' , \
timeit(stmt, setup="from __main__ import DecodeAES, cipher, iv_bytes, encoded, M", number=rep) / rep


## Diffie Hellman benchmark
a = DiffieHellman()
b = DiffieHellman()
a.genKey(b.publicKey)
b.genKey(a.publicKey)

# compute timing of performing modular exponentiation
print 'time to perform modular exponentiation: ', \
timeit("pow(b.publicKey, a.privateKey, a.prime)", setup="from __main__ import a, b", number=rep) / rep