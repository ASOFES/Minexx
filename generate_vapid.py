from py_vapid import Vapid01 as Vapid

private_key, public_key = Vapid.create_keypair()
print("VAPID PRIVATE KEY:", private_key.decode())
print("VAPID PUBLIC KEY:", public_key.decode())