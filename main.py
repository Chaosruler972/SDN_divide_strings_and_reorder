import random

from onetimepad import encrypt

from server import Controller

message = "Unencrypted message"
one_time_pad_xor_key = str(random.getrandbits(2 ** len(message)))
pad = encrypt(message, one_time_pad_xor_key)

c = Controller(pad, one_time_pad_xor_key)
c.send_string()

c2 = Controller(c, None)

c2.send_message_to_other_controller(c)

result_string = c2.print_message()

print("Resulting string: %s" % result_string)
