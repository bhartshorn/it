import socket
import threading
import select
import time
import string
import argparse
import signal
import sys
from player import Player
from collections import deque

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="port number to connect to")
parser.add_argument("-i", "--ip", help="ip address to connect to")
args = parser.parse_args()

quit = False

players = {}

def get_first_player_free(players):
    for key in range(1, 256):
        if key not in players:
            return key
    return -1

def handler_sigint(signal, frame):
    global quit
    quit = True
    print("\nRecieved SIGINT, server exiting")

signal.signal(signal.SIGINT, handler_sigint)

class ClientThread(threading.Thread):
    def __init__(self, client_sock, address, id):
        threading.Thread.__init__(self)
        self.sock = client_sock
        # self.sock.setblocking(0)
        self.sock.settimeout(0.01)
        self.address = address
        self.id = id
        self.recv_q = deque()
        self.recv_buf = ""
        self.quit = False

    def recieve(self):
        # TODO: try-catch
        try:
            buffer = self.recv_buf + self.sock.recv(2048)
        except socket.timeout as msg:
            return True
        except socket.error as msg:
            print("Could not recieve, socket closed", msg)
            return False
        if len(buffer) == 0:
            return True

        self.recv_buf = ""
        split = string.split(buffer)
        if (buffer[-1] != "\n"):
            self.recv_buf = split[-1]
            del split[-1]

        for field in split:
            self.recv_q.append(field)

        return True

    def close(self):
        print("Player {} quit".format(self.id))
        try:
            self.sock.send("q".encode('utf-8'))
        except socket.error as msg:
            print("Player {} disconnected".format(self.id))

        try:
            del players[self.id]
        except KeyError as msg:
            print("Player {} already deleted".format(self.id))

        try:
            self.sock.close()
        except socket.error as msg:
            print(msg)

        self.quit = True


    def run(self):
        global quit

        # Server log
        print("Player {} connected".format(self.id))

        # Create new player for this connection
        players[self.id] = Player(self.id)

        # send the client his id
        self.sock.send(("i:{}\n".format(self.id)).encode('utf-8'))

        while not quit and not self.quit:
            if not self.recieve():
                self.close()

            while len(self.recv_q) > 0:
                input = string.split(self.recv_q.popleft(), ":")
                if input[0] == "q":
                    self.close()
                elif input[0] == "m":
                    players[self.id].move(input)
                elif input[0] == "c" and input[3] != "":
                    players[self.id].player_char = input[2]
                    players[self.id].player_color = input[3]
                    print("Player {} changed character to {}".format(self.id, input[2]))
                else:
                    print(input)

        self.close()

def update_clients(client_sockets, players):
    global quit

    while not quit:
        time.sleep(0.01)

        # Send player statuses to clients
        for i, p in players.viewitems():
            for j, s in client_sockets.viewitems():
                try:
                    s.send(p.to_network().encode('utf-8'))
                except socket.error as msg:
                    #print("Player {} seems to have disconnected".format(i))
                    continue

        if len(players) == 0:
            continue

        # check collision and check possession
        player_with_ball = -1
        p_loc_x = -1
        p_loc_y = -1

        for i, p in players.viewitems():
            if p.has_ball:
                player_with_ball = p.player_id
                p_loc_x = p.loc_x
                p_loc_y = p.loc_y

        if player_with_ball == -1:
            for key in range(1, 256):
                if key in players:
                    player_with_ball = key
                    players[key].has_ball = True
                    p_loc_x = players[key].loc_x
                    p_loc_y = players[key].loc_y
                    break

        for i, p in players.viewitems():
            if (not i == player_with_ball) and p.loc_x == p_loc_x and p.loc_y == p_loc_y:
                if p.give_ball() == True:
                    players[player_with_ball].take_ball()

        players[player_with_ball].num_points += 0.01



def main():
    global quit
    # set up socket parameters
    port = 11000
    ip = ""
    if args.port:
        port = args.port

    if args.ip:
        ip = args.ip

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((ip, port))
    server_sock.settimeout(1.5)
    server_sock.listen(10)

    # TODO: Create thread to send updates to all clients at the same time
    #       and check for collision/update who has ball. Collect sockets
    #       in a container to pass to thread, only send on that thread
    client_sockets = {}
    threads = []

    t = threading.Thread(target=update_clients, args=(client_sockets, players))
    threads.append(t)
    t.start()
    print("Waiting on Client...")
    while not quit:
        try:
            (client_sock, address) = server_sock.accept()
        except socket.timeout, err:
            pass
        except IOError, err:
            # Error "Interrupted system call" should make program quit
            if err.errno and err.errno == 4:
                quit = True
            else:
                print(err)
        else:
            next_id = get_first_player_free(players)
            client_sockets[next_id] = client_sock
            t = ClientThread(client_sock, address, next_id)
            threads.append(t)
            t.start()

    for t in threads:
        t.join()

    print("Closing server cleanly")
    server_sock.shutdown(socket.SHUT_RDWR)
    server_sock.close()
    sys.exit()

if __name__ == "__main__":
    main()
