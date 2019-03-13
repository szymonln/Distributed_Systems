import socket
import sys
from threading import Thread
import time

NEW_NODE = "new_node"
NEW_NODE_ANSWER = "new_node_anwser"
TOKEN = "token"
MESSAGE = "message"
my_ip_address = None
my_port = None
is_token = None
my_socket = None
next_ip_address = None
next_port = None
id = None
message_to_send = None
logger_ip_address = "230.1.1.1"
logger_port = 12345


def new_message(type, destination_ip_address, message):
    return type + " " + destination_ip_address + " " + message;


def is_msg_for_me(message):
    if message.split()[1] == my_ip_address:
        return True
    else:
        return False


def get_message_type(message):
    return message.split(" ")[0]


def get_message_counter(buff):
    message = str(buff, 'utf-8')
    return int(message.split(" ")[3])


def decrement_message_counter(buff):
    message = str(buff, 'utf-8')
    message_as_list = message.split(" ")
    destination_ip_address = message_as_list[1]
    content = message_as_list[2]
    counter = int(message_as_list[3])
    counter = counter - 1
    return bytes(MESSAGE + " " + destination_ip_address + " " + content + " " + str(counter), 'utf-8')


def listening():
    global my_socket
    global next_ip_address
    global is_token
    global next_port
    buff = []
    while True:
        buff, address = my_socket.recvfrom(1024)
        type = get_message_type(str(buff, 'utf-8'))
        if type == MESSAGE:
            if is_msg_for_me(str(buff, 'utf-8')):
                print("\033[92mRecieved message: " + str(buff, 'utf-8').split(" ", 2)[2].rsplit(" ", 1)[0])
                print("\033[92mSend message format:[ip message]:")
                Thread(target=handle_token).start()
            else:
                print("\033[92mTransferring a message")
                message_counter = get_message_counter(buff)
                if message_counter > 0:
                    buff = decrement_message_counter(buff)
                    my_socket.sendto(buff, (next_ip_address, next_port))
                else:
                    print("\033[93mThis IP does not exist in the network.")
        elif type == TOKEN:
            Thread(target=handle_token).start()
        elif type == NEW_NODE:
            buff = NEW_NODE_ANSWER + " " + next_ip_address + " " + str(next_port)
            my_socket.sendto(bytes(buff, 'utf-8'), address)
            next_ip_address = address[0]
            next_port = address[1]
        else:
            next_ip_address = str(buff, 'utf-8').split(" ")[1]
            next_port = int(str(buff, 'utf-8').split(" ")[2])
            print("\033[92m***connected***")


def send_new_message():
    global my_socket
    global is_token
    while True:
        print("\033[92mSend message format:[ip message]:")
        input_ = input()
        destination_ip_address = input_.split(" ")[0]
        message = input_.split(" ")[1]
        # print("Your message: " + destination_ip_address + " " + message)
        buff = MESSAGE + " " + destination_ip_address + " " + message + " " + str(10)
        while is_token is False:
            print("\033[92m....Waiting for token")
            time.sleep(1)
        my_socket.sendto(bytes(buff, 'utf-8'), (next_ip_address, next_port))
        is_token = False


def handle_token():
    global is_token
    is_token = True
    time.sleep(1)
    is_token = False
    buff = TOKEN
    my_socket.sendto(bytes(buff, 'utf-8'), (next_ip_address, next_port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    sock.sendto(bytes(id + " got token", 'utf-8'), (logger_ip_address, logger_port))


def add_node():
    buff = NEW_NODE + " " + my_ip_address + " " + str(my_port)
    my_socket.sendto(bytes(buff, 'utf-8'), (next_ip_address, next_port))


def main(**kwargs):
    global my_socket
    global my_ip_address
    global my_port
    global is_token
    global my_socket
    global next_ip_address
    global next_port
    global id

    id = kwargs["id"]
    my_ip_address = kwargs["my_ip"]
    my_port = int(kwargs["my_port"])
    next_ip_address = kwargs["next_ip"]
    next_port = int(kwargs["next_port"])
    token = kwargs.get("token") or None
    if token:
        is_token = True
    else:
        is_token = False

    print(my_ip_address + " " + str(my_port))

    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.bind((my_ip_address, my_port))

    if is_token:
        Thread(target=handle_token).start()
    else:
        add_node()

    Thread(target=listening).start()
    Thread(target=send_new_message).start()


if __name__ == "__main__":
    main(**dict(arg.split(":") for arg in sys.argv[1:]))

