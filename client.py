import socket
import string
import select
import time
import threading
import argparse
import pygame
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

def game_loop(screen, send_q, recv_q):
    global quit
    clock = pygame.time.Clock()
    lib_sans = pygame.font.SysFont('Liberation Sans', 30)
    scores_surface = pygame.Surface((200, 600))
    bg_play = pygame.Color("#474747")
    bg_scores = pygame.Color("black")
    dia_circle_outer = 10
    dia_circle_inner = 5
    players = {}
    last_command = ""
    my_id = 1

    screen.fill(bg_play)

    while not quit:
        screen.fill(bg_play)
        scores_surface.fill(bg_scores)
        command = ""

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                send_q.append("q:{}\n".format(my_id))
                quit = True

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_LEFT] or pressed[pygame.K_h]:
            send_q.append("m:{}:l\n".format(my_id))
        if pressed[pygame.K_RIGHT] or pressed[pygame.K_l]: 
            send_q.append("m:{}:r\n".format(my_id))
        if pressed[pygame.K_UP] or pressed[pygame.K_k]:
            send_q.append("m:{}:u\n".format(my_id))
        if pressed[pygame.K_DOWN] or pressed[pygame.K_j]:
            send_q.append("m:{}:d\n".format(my_id))

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
        #print(command)

        font_height = lib_sans.get_height()
        score_y = font_height + 5
        score_x = 5

        for i, p in players.viewitems():
            if (i == my_id):
                player_color = pygame.Color("blue")
            else:
                player_color = pygame.Color("red")

            if (p.has_ball):
                player_color = pygame.Color("green")

            # Draw player's score
            player_score = "{:<4} {:>4}".format(i, p.num_points)
            scores_surface.blit(lib_sans.render(player_score, True, player_color), (score_x, score_y))

            # Draw player on screen
            draw_x = (p.loc_x * dia_circle_outer) + dia_circle_outer
            draw_y = (p.loc_y * dia_circle_outer) + dia_circle_outer
            pygame.draw.circle(screen, player_color, [draw_x, draw_y], dia_circle_outer, dia_circle_inner)

            #update score y loc
            score_y = score_y + font_height + 5

        lib_sans.set_underline(True)
        scores_surface.blit(lib_sans.render("SCORES", True, pygame.Color("white")), (score_x, 5))
        lib_sans.set_underline(False)
        screen.blit(scores_surface, (600, 0))
        # Refresh the screen
        pygame.display.update()
        clock.tick(10)


def main():
    # set up socket parameters
    port = 11000
    ip = "localhost"
    if args.port:
        port = args.port

    if args.ip:
        ip = args.ip

    # set up pygame
    pygame.init()
    game_window = pygame.display.set_mode((800, 600))

    # set up the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #TODO: Attempt connecting on higher ports automatically -- The Unix Way?
    sock.connect((ip, port))

    send_q = deque()
    recv_q = deque()
    network_thread = NetworkThread(sock, send_q, recv_q)
    network_thread.start()

    game_loop(game_window, send_q, recv_q)
    #curses.wrapper(game_loop, send_q, recv_q)

    sock.close()


if __name__ == "__main__":
    main()
