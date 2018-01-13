from server import Controller

c = Controller("Unencrypted message")
c.send_string()


c2 = Controller(c)

c2.send_message_to_other_controller(c)

result_string = c2.print_message()

print("Resulting string: %s" % result_string)
