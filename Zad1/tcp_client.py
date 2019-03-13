import socket
import sys
from threading import Thread
import time
import random
import struct

NEW_SOCKET_ALERT_IP_ADDRESS = "230.1.1.2"
NEW_SOCKET_ALERT_PORT = 12346
LOGGER_IP_ADDRESS = "230.1.1.1"
LOGGER_PORT = 12345
BUFFER_SIZE = 40
NEW_NODE = "new_node"
NEW_NODE_ANSWER = "new_node_anwser"
TOKEN = "token"
MESSAGE = "message"
NEW_TOKEN = "new_token"
DELETE_TOKEN = "delete_token"
recieving_ip = None
recieving_port = None
new_node_port = None
is_token = None
receiving_socket = None
sending_socket = None
new_token_socket = None
new_node_socket = None
next_ip_address = None
next_port = None
id = None
token_to_delete = None
token_id = None
token_sender = False
token_to_set = None


def decrement_message_counter(buff):
    message = str(buff, 'utf-8')
    message_as_list = message.split(" ")
    destination_ip_address = message_as_list[1]
    content = message_as_list[2]
    counter = int(message_as_list[-1])
    counter = counter - 1
    return bytes(MESSAGE + " " + destination_ip_address + " " + content + " " + str(counter), 'utf-8')


def get_message_type(message):
    return message.split(" ")[0]


def get_message_counter(buff):
    message = str(buff, 'utf-8')
    return int(message.rsplit(" ")[-1])


def prep_message(type, destination_ip_address, message):
    return type + " " + destination_ip_address + " " + message


def is_msg_for_me(message):
    if message.split()[1] == recieving_ip:
        return True
    else:
        return False


def listening():
    global next_ip_address
    global next_port
    global token_id
    while True:
        connection, address = receiving_socket.accept()
        buff_1 = connection.recv(BUFFER_SIZE)
        type = get_message_type(str(buff_1, 'utf-8'))
        if type == MESSAGE:
            if is_msg_for_me(str(buff_1, 'utf-8')):
                print("\033[92mRecieved message: \x1b[6;30;42m" + str(buff_1, 'utf-8').split(" ",2)[2].rsplit(" ", 1)[0]
                      + "\x1b[0m")
                print("\033[92mSend message format:[ip message]:")
            else:
                print("\033[92mTransferring a message")
                message_counter = get_message_counter(buff_1)
                if message_counter > 0:
                    buff_1 = decrement_message_counter(buff_1)
                    sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sending_socket.connect((next_ip_address, next_port))
                    sending_socket.send(buff_1)
                    sending_socket.close()
                else:
                    print("\033[91mThis IP does not exist in the network.")
        elif type == TOKEN:
            if token_id is None:
                token_id = int(str(buff_1, 'utf-8').split(" ")[1])
            Thread(target=token_handle).start()
        elif type == NEW_NODE:
            buff_2 = NEW_NODE_ANSWER + " " + next_ip_address + " " + str(next_port)
            next_ip_address = str(buff_1, 'utf-8').split(" ")[1]
            next_port = int(str(buff_1, 'utf-8').split(" ")[2])
            connection.send(bytes(buff_2, 'utf-8'))


def send_new_message():
    global sending_socket
    global is_token
    while True:
        print("\033[92mSend message format: [ip] [message]:")
        input_ = input()
        destination_ip_address = input_.split(" ")[0]
        message = input_.split(" ", 1)[1]
        buff = MESSAGE + " " + destination_ip_address + " " + message + " " + str(10)
        while is_token is False:
            print("\033[92m....Waiting for token")
            time.sleep(1)
        sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sending_socket.connect((next_ip_address, next_port))
        sending_socket.send(bytes(buff, 'utf-8'))
        sending_socket.close()
        is_token = False


def token_handle():
    global is_token
    global sending_socket
    global token_sender
    global token_to_delete
    global token_id
    global token_to_set

    is_token = True
    time.sleep(1)
    is_token = False
    buff = TOKEN + " " + str(token_id)
    if token_sender == True and token_to_delete == token_id:
        print("\033[91mToken " + str(token_id) + " is not forwarded")
        token_sender = False
        token_to_delete = None
        token_id = token_to_set
        token_to_set = None
        token_sender = False
        add_node()
        print("\033[92mSend message format:[ip message]:")
    else:
        sending_socket.close()
        sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sending_socket.connect((next_ip_address, next_port))
        sending_socket.send(bytes(buff, 'utf-8'))

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        sock.sendto(bytes(id + " GOT TOKEN", 'utf-8'), (LOGGER_IP_ADDRESS, LOGGER_PORT))


def add_node():
    global sending_socket
    global next_ip_address
    global next_port
    buff = NEW_NODE + " " + recieving_ip + " " + str(recieving_port)
    sending_socket.connect((next_ip_address, next_port))
    sending_socket.send(bytes(buff, 'utf-8'))
    data = sending_socket.recv(BUFFER_SIZE)
    next_ip_address = str(data, 'utf-8').split(" ")[1]
    next_port = int(str(data, 'utf-8').split(" ")[2])
    print("\033[92m**connected**")
    sending_socket.close()


def send_new_token_information():
    print("\033[92mNew token " + str(token_id) + " in network")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(bytes(NEW_TOKEN + " " + str(token_id), 'utf-8'), (NEW_SOCKET_ALERT_IP_ADDRESS, NEW_SOCKET_ALERT_PORT))


def listen_for_unproper_tokens():
    global token_to_delete
    global token_id
    global token_to_set
    buff = []
    while True:
        buff = new_token_socket.recv(30)
        if str(buff, 'utf-8').split(" ")[0] == NEW_TOKEN:
            if token_sender:
                new_token = int(str(buff, 'utf-8').split(" ")[1])
                if new_token != token_id:
                    token_to_delete = new_token
                    print("Token " + str(token_to_delete) + " has to be deleted!")
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
                    sock.sendto(
                        bytes(DELETE_TOKEN + " " + str(token_to_delete) + " " + str(token_id), 'utf-8'),
                        (NEW_SOCKET_ALERT_IP_ADDRESS, NEW_SOCKET_ALERT_PORT))
        if str(buff, 'utf-8').split(" ")[0] == DELETE_TOKEN:
            if token_sender:
                if token_id == int(str(buff, 'utf-8').split(" ")[1]):
                    token_to_delete = token_id
                    token_to_set = int(str(buff, 'utf-8').split(" ")[2])


def main(**kwargs):
    global receiving_socket
    global sending_socket
    global new_node_socket
    global is_token
    global token_id
    global new_token_socket
    global token_sender
    global recieving_ip

    global recieving_ip
    global recieving_port
    global new_node_port
    global is_token
    global receiving_socket
    global sending_socket
    global new_node_socket
    global next_ip_address
    global next_port
    global id

    id = kwargs["id"]
    recieving_ip = kwargs["recieving_ip"]
    recieving_port = int(kwargs["recieving_port"])
    new_node_port = int(kwargs["new_node_port"])
    next_ip_address = kwargs["next_ip"]
    next_port = int(kwargs["next_port"])
    token = kwargs.get("token") or None
    if token:
        i_have_token = True
    else:
        i_have_token = False

    print("My ip: " + recieving_ip + "  recieving port: " + str(recieving_port))
    print("My ip: " + recieving_ip + "  new node port: " + str(new_node_port))
    print("Next ip: " + next_ip_address + "   next port: " + str(next_port) + "\n")

    receiving_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    receiving_socket.bind((recieving_ip, recieving_port))
    receiving_socket.listen(1)

    sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    new_node_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    new_node_socket.bind((recieving_ip, new_node_port))
    new_node_socket.listen(1)

    new_token_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    new_token_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    new_token_socket.bind((NEW_SOCKET_ALERT_IP_ADDRESS, NEW_SOCKET_ALERT_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(NEW_SOCKET_ALERT_IP_ADDRESS), socket.INADDR_ANY)
    new_token_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    if i_have_token:
        token_sender = True
        token_id = random.randint(100, 999)
        Thread(target=token_handle).start()
        send_new_token_information()
    else:
        add_node()

    Thread(target=listen_for_unproper_tokens).start()
    Thread(target=listening).start()
    Thread(target=send_new_message).start()


if __name__ == "__main__":
    main(**dict(arg.split(":") for arg in sys.argv[1:]))
