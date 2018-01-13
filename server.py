import random
from multiprocessing.dummy import Pool as ThreadPool

import onetimepad
from Crypto.PublicKey import RSA

debug = 0

default_bits_for_encryption = 1024


class Server:
    def __init__(self, server_index: int, size_in_bits: int = default_bits_for_encryption):
        """

        :param server_index - index of server in the arr (printing status only):
        :param size_in_bits - the size of the RSA key to generate in bits:
        """
        self.payload = 0
        self.key = RSA.generate(size_in_bits)
        self.index = server_index

    def get_pub(self) -> RSA.pubkey:
        """

        :return: current server public RSA key (for communication purposes)
        """
        return self.key.publickey()

    def store_message(self, message: int) -> None:
        """

        :param message: stores corrent message here, a single-value buffer, value is decrypted after
            being recieved
        """
        if debug == 1:
            print(f"Server at index {self.index:d} Successfully recieved message : {message}")
        self.payload = self.key.decrypt(message)

    def send_back(self, key) -> (int, int):
        """

        :param key: the key to encrypt current message
        :return: the current message in an encrypted form (never send raw)
        """
        server_key = key.publickey()
        encrypted_message = server_key.encrypt(int(self.payload), 32)
        if debug == 1:
            print("Server at index %d Successfully sent message : %d" % (self.index, encrypted_message[0]))
        return encrypted_message, self.index

    def send_my_message(self, other_server: __init__) -> None:
        """

        :param other_server: another Server
            Sends current message to another server using their public key
        """
        server_key = other_server.get_pub()
        encrypted_message = server_key.encrypt(int(self.payload), 32)
        other_server.store_message(encrypted_message)


class Controller:
    def __init__(self, whatever_was_sent, one_time_pad_xor_key):
        """

        :type whatever_was_sent: Could be a Controller, therefore I "clone" the controller's amount of
                    Servers just so I will have enough to render the string
        Can be a message to to make a new Controller that will divide that string to n/2 servers
        """
        if type(whatever_was_sent) is Controller:
            self.arr = []
            self.arr_size = whatever_was_sent.arr_size
            for i in range(0, self.arr_size):
                self.arr.append(Server(i))
        else:
            whatever_was_sent = onetimepad.decrypt(whatever_was_sent, one_time_pad_xor_key)
            if len(whatever_was_sent) % 2 != 0:
                whatever_was_sent = whatever_was_sent + " "
            self.message = whatever_was_sent
            print("Recieved string to send: %s" % whatever_was_sent)
            self.arr = []
            self.arr_size = int(len(whatever_was_sent) / 2) + 1
            for i in range(0, self.arr_size):
                self.arr.append(Server(i))
        self.key = RSA.generate(default_bits_for_encryption)

    def send_specific_string(self,i:int) -> None:
        substr = self.message[i * 2:i * 2 + 2]
        int_message = int.from_bytes(substr.encode('utf-8'), 'little')
        server_key = self.arr[i].get_pub()
        encrypted_message = server_key.encrypt(int_message, 32)
        self.arr[i].store_message(encrypted_message)

    def send_string(self) -> None:
        """
            Sends the current configured strings to all my servers
            this function uses multiprocessing to make our sending "more crazy and random"
            to simulate more reality of manner
        """
        randomized_range = self.create_random_range_between_0_and_n(self.arr_size)
        pool = ThreadPool(self.arr_size)
        results = pool.map(self.send_specific_string, randomized_range)
        pool.close()
        pool.join()

    def send_message_to_other_controller(self, other_controller: __init__) -> None:
        """
        :param other_controller: the other controller that will recieve my message
            my controller's server will each find one server to send one part of the string
            (preferrebly by the index position, but can be avoided due to TCP)
        """
        for i in range(0, self.arr_size):
            other_controller.arr[i].send_my_message(self.arr[i])

    def send_result_back_of_server_by_index(self, index) -> (int, int):
        if debug == 1:
            print("Requesting from server at index %d\n" % index)
        return self.arr[index].send_back(self.key.publickey())

    @staticmethod
    def create_random_range_between_0_and_n(n: int) -> list:
        pseudo_random_number_generated_array = []
        list_of_numbers = []
        for i in range(0,n):
            list_of_numbers.append(i)
        while len(list_of_numbers) != 0:
            elem = list_of_numbers.pop(random.randint(0, len(list_of_numbers) - 1))
            pseudo_random_number_generated_array.append(elem)
        return pseudo_random_number_generated_array

    def print_message(self) -> str:
        """
            Uses our controller's key to get our servers to send their string to us
            this function is using parallel computation (CPU multiprocess, not multithreading)
            in order to "randomize" our results (which will be re-ordered at later date)
        """
        randomized_range = self.create_random_range_between_0_and_n(self.arr_size)
        pool = ThreadPool(self.arr_size)
        results = pool.map(self.send_result_back_of_server_by_index, randomized_range)
        pool.close()
        pool.join()
        string = ""
        for i in range(0, self.arr_size):
            encrypted_message_from_server, server_index = results[i]
            num = self.key.decrypt(encrypted_message_from_server)
            results[i] = num.to_bytes((num.bit_length() + 7) // 8, 'little').decode('utf-8'), server_index

        for i in range(0, self.arr_size):
            substr = ""
            for j in range(0, self.arr_size):
                message, index = results[j]
                if i == index:
                    substr = message
            string += substr
        if debug == 1:
            print("Resulting string: %s" % string)
        return string
