import socket
import string
import select
import time
import threading
import argparse
import pygame
from pygame import gfxdraw
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

    # Colors -- maybe should be elsewhere? dunno
    colors = {'1': pygame.Color("#83CC67"),
              '2': pygame.Color("#CB66C5"),
              '3': pygame.Color("#B83D4E"),
              '4': pygame.Color("#F61EC6"),
              '5': pygame.Color("#1EEAF6"),
              '6': pygame.Color("#1E96F6"),
              '7': pygame.Color("#F6EA1E"),
              '8': pygame.Color("#F68C1E"),
              'scores_border': pygame.Color("#9B9B9B"),
              'white': pygame.Color("white")}

    # Set up play area surface
    bg_play = pygame.Color("black")
    screen.fill(bg_play)

    # Set up scores surface
    scores_surface = pygame.Surface((200, 600))
    bg_scores = pygame.Color("#575757")
    scores_surface.fill(bg_scores)
    score_x = 12

    # Set up font for scores
    lib_sans = pygame.font.SysFont('Liberation Sans', 30)
    font_height = lib_sans.get_height()
    font_offset = font_height + 5

    # Set up scores header
    lib_sans.set_underline(True)
    scores_header = lib_sans.render("scores", True, colors['white'])
    lib_sans.set_underline(False)
    offset_scores_header = (200 - scores_header.get_width()) / 2

    # Set up circle parameters
    circle_radius = 10
    circle_radius_inner = 5

    # Game state
    players = {}
    my_id = 1



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

        score_y = font_offset

        for i, p in players.viewitems():
            # Draw player on screen
            if (p.has_ball):
                draw_x = (p.loc_x * circle_radius)
                draw_y = (p.loc_y * circle_radius)
                pygame.draw.rect(screen, colors[str(i)], [draw_x, draw_y, circle_radius * 2, circle_radius * 2])
                pygame.draw.rect(screen, bg_play, [draw_x + (circle_radius / 2), draw_y + (circle_radius / 2), circle_radius, circle_radius])
            else:
                draw_x = (p.loc_x * circle_radius) + circle_radius
                draw_y = (p.loc_y * circle_radius) + circle_radius

                # Yeah... this is harder than it needs to be!
                gfxdraw.aacircle(screen, draw_x, draw_y, circle_radius, colors[str(i)])
                gfxdraw.filled_circle(screen, draw_x, draw_y, circle_radius, colors[str(i)])
                gfxdraw.aacircle(screen, draw_x, draw_y, circle_radius_inner, bg_play)
                gfxdraw.filled_circle(screen, draw_x, draw_y, circle_radius_inner, bg_play)


            # Draw player's score
            scores_surface.blit(lib_sans.render(str(i), True, colors[str(i)]), (score_x, score_y))
            score = lib_sans.render(str(p.num_points), True, colors['white'])
            scores_surface.blit(score, (200 - score.get_width() - score_x, score_y))


            #update score y loc
            score_y = score_y + font_offset

        pygame.draw.line(scores_surface, colors['scores_border'], [0, 0], [0, 600], 5)
        scores_surface.blit(scores_header, (offset_scores_header, 5))
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
