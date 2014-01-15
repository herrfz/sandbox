#!/usr/bin/env python
'''
code from: http://blog.markloiseau.com/2013/01/diffie-hellman-tutorial-in-python/
'''
from binascii import hexlify
import hashlib

# If a secure random number generator is unavailable, exit with an error.
try:
	import Crypto.Random.random
	secure_random = Crypto.Random.random.getrandbits
except ImportError:
	import OpenSSL
	secure_random = lambda x: long(hexlify(OpenSSL.rand.bytes(x>>3)), 16)

class DiffieHellman(object):
    """
	An implementation of the Diffie-Hellman protocol.
	This class uses primes in MODP Group from RFC 3526, stored in the prime_file.
	"""
    def __init__(self, prime_file='3072bit_prime.txt', private_key_len=256):
        """
        Generate the public and private keys.
        """
        with open(prime_file, 'r') as f: 
            self.prime = int(f.read().replace(' ', '').replace('\n', ''), 16)
        
        self.generator = 2
        self.privateKey = self.genPrivateKey(private_key_len)
        self.publicKey = self.genPublicKey()

    def genPrivateKey(self, bits):
        """
        Generate a private key using a secure random number generator.
        """
        return secure_random(bits)

    def genPublicKey(self):
        """
        Generate a public key X with g**x % p.
        """
        return pow(self.generator, self.privateKey, self.prime)

    def checkPublicKey(self, otherKey):
        """
        Check the other party's public key to make sure it's valid.
        Since a safe prime is used, verify that the Legendre symbol is equal to one.
        """
        if(otherKey > 2 and otherKey < self.prime - 1):
            if(pow(otherKey, (self.prime - 1)/2, self.prime) == 1):
                return True
        return False

    def genSecret(self, privateKey, otherKey):
        """
        Check to make sure the public key is valid, then combine it with the
        private key to generate a shared secret.
        """
        if(self.checkPublicKey(otherKey)==True):
            sharedSecret = pow(otherKey, privateKey, self.prime)
            return sharedSecret
        else:
            raise Exception("Invalid public key.")

    def genKey(self, otherKey):
        """
        Derive the shared secret, then hash it to obtain the shared key.
        """
        self.sharedSecret = self.genSecret(self.privateKey, otherKey)
        s = hashlib.sha256()
        s.update(str(self.sharedSecret))
        self.key = s.digest()

    def getKey(self):
        """
        Return the shared secret key
        """
        return self.key

    def showParams(self):
        """
        Show the parameters of the Diffie Hellman agreement.
        """
        print "Parameters:"
        print
        print "Prime: ", self.prime
        print "Generator: ", self.generator
        print "Private key: ", self.privateKey
        print "Public key: ", self.publicKey
        print

    def showResults(self):
        """
        Show the results of a Diffie-Hellman exchange.
        """
        print "Results:"
        print
        print "Shared secret: ", self.sharedSecret
        print "Shared key: ", hexlify(self.key)
        print