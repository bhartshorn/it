import curses
import socket
import string
import select
import time
import threading
import argparse
from player import Player
from collections import deque

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="port number to connect to")
parser.add_argument("-i", "--ip", help="ip address to connect to")
args = parser.parse_args()
quit = False

class NetworkThread(threading.Thread):
    recv_buf = ""

    def __init__(self, sock, send_q, recv_q):
        threading.Thread.__init__(self)
        self.sock = sock
        self.send_q = send_q
        self.recv_q = recv_q


    def run(self):
        global quit
        while not quit:
            readable, w, e = select.select([self.sock],[],[],10)
            if len(readable) > 0:
                self.recieve()

            if len(self.send_q) > 0:
                self.send()

    def send(self):
        # TODO: try-catch
        while len(self.send_q) > 0:
            self.sock.send(self.send_q.popleft())

    def recieve(self):
        # TODO: try-catch
        buffer = self.recv_buf + self.sock.recv(2048)
        if len(buffer) == 0:
            return

        self.recv_buf = ""
        split = string.split(buffer)
        if (buffer[-1] != "\n"):
            self.recv_buf = split[-1]
            del split[-1]

        for field in split:
            self.recv_q.append(field)


def game_loop(stdscr, send_q, recv_q):
    global quit
    players = {}
    k = 0
    last_command = ""
    my_id = 1

    # Clear and refresh the screen for a blank canvas
    stdscr.erase()
    stdscr.refresh()
    stdscr.nodelay(True)
    height, width = stdscr.getmaxyx()

    game_window = stdscr.subwin(28, 80, 0, 0)
    scores_window = stdscr.subwin(28, width - 80, 0, 80)

    # Start colors in curses
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK) 
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_WHITE)

    curses.curs_set(0)
    #curses.resizeterm(28, 80)

    # Loop where k is the last character pressed
    while not quit:
        # get next input
        k = stdscr.getch()
        move = ""

        # Initialization
        game_window.erase()

        if k == curses.KEY_DOWN or k == ord('j'):
            move = "d"
        elif k == curses.KEY_UP or k == ord('k'):
            move = "u"
        elif k == curses.KEY_RIGHT or k == ord('l'):
            move = "r"
        elif k == curses.KEY_LEFT or k == ord('h'):
            move = "l"
        elif k == ord('p'):
            prompt_message = "Please enter the 'Character' you would like to be"
            prompt = stdscr.subwin(3,len(prompt_message) + 4, 13, 10)
            prompt.attron(curses.color_pair(1))
            prompt.border()
            prompt.attroff(curses.color_pair(1))
            prompt.addstr(1,2, prompt_message)
            prompt.refresh()
            c = -1
            while (c > 126 or c < 33):
                c = prompt.getch()
            send_q.append("c:{}:{}\n".format(my_id, chr(c)))

        elif k == ord('q'):
            send_q.append("q:{}\n".format(my_id))
            quit = True

        if move != "":
            send_q.append("m:{}:{}\n".format(my_id, move))


        while len(recv_q) > 0:
            command = string.split(recv_q.popleft(), ":")
            if command[0] == "q":
                quit = True
            elif command[0] == "i":
                my_id = int(command[1])
            elif command[0] == "p" and len(command) >= 2:
                p_id = int(command[1])
                if int(p_id) in players:
                    players[p_id].parse_network(command)
                else:
                    new_player = Player(p_id)
                    players[p_id] = new_player

            last_command = command

        #create statusbar string
        statusbarstr = "Press 'q' to exit | ID: {} | Command: {}".format(my_id, last_command)
        # Render status bar
        game_window.attron(curses.color_pair(3))
        game_window.addstr(26, 1, statusbarstr)
        game_window.addstr(26, len(statusbarstr) + 1, " " * (79 - len(statusbarstr)))
        game_window.attroff(curses.color_pair(3)) 
        game_window.border()
        game_window.addstr(0, 2, "GAME")

        scores_window.border()
        scores_window.addstr(0, 2, "SCORES")
        scores_next_y = 1
        #render Players
        for i, p in players.viewitems():
            if (i == my_id):
                player_color = curses.color_pair(2)
            else:
                player_color = curses.color_pair(0)

            if (p.has_ball):
                player_color = player_color | curses.A_REVERSE

            game_window.addstr(p.loc_y+1, p.loc_x+1, p.player_char, player_color)
            scores_window.addstr(scores_next_y, 2, "{}: {}".format(i, p.num_points))
            scores_next_y += 1

        # Refresh the screen
        game_window.refresh()
        scores_window.refresh()
        time.sleep(0.005)

    # When game loop is finished
    exit()

def main():
    # set up socket parameters
    port = 11000
    ip = "localhost"
    if args.port:
        port = args.port

    if args.ip:
        ip = args.ip

    # set up the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #TODO: Attempt connecting on higher ports automatically -- The Unix Way?
    sock.connect((ip, port))

    send_q = deque()
    recv_q = deque()
    network_thread = NetworkThread(sock, send_q, recv_q)
    network_thread.start()

    curses.wrapper(game_loop, send_q, recv_q)

    sock.close()


if __name__ == "__main__":
    main()
