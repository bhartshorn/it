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

# Colors
colors = {'1':              pygame.Color("#5BB668"),
          '2':              pygame.Color("#B6815B"),
          '3':              pygame.Color("#B6635B"),
          '4':              pygame.Color("#B6B35B"),
          '5':              pygame.Color("#92B65B"),
          '6':              pygame.Color("#5BABB6"),
          '7':              pygame.Color("#B65BA9"),
          '8':              pygame.Color("#715BB6"),
          'bg_menu':        pygame.Color("#575757"),
          'scores_border':  pygame.Color("#9B9B9B"),
          'white':          pygame.Color("#FFFFFF")}

# To be populated in main()
fonts = {}

class GuiButton():
    def __init__(self, label, pos):
        self.label = label
        self.pos = pos
        #self.font = font
        self.highlighted = False

        self.text_n = fonts['sm'].render(label, 1, colors['scores_border'])
        self.button_n = pygame.Surface((100, self.text_n.get_height() + 16))
        self.button_n.fill(colors['scores_border'])
        pygame.draw.rect(self.button_n, colors['bg_menu'], [2, 2, self.button_n.get_width() - 4, self.button_n.get_height() - 4])

        self.button_n.blit(self.text_n, ((100 - self.text_n.get_width()) / 2, 8))

        self.text_h = fonts['sm'].render(label, 1, colors['white'])
        self.button_h = pygame.Surface((100, self.text_h.get_height() + 16))
        self.button_h.fill(colors['white'])
        pygame.draw.rect(self.button_h, colors['bg_menu'], [2, 2, self.button_h.get_width() - 4, self.button_h.get_height() - 4])

        self.button_h.blit(self.text_h, ((100 - self.text_h.get_width()) / 2, 8))

    def draw(self, surface):
        if self.highlighted:
            surface.blit(self.button_h, (self.pos[0], self.pos[1]))
        else:
            surface.blit(self.button_n, (self.pos[0], self.pos[1]))

    def test_mouse(self, pos):
        x_loc = pos[0]
        y_loc = pos[1]

        if x_loc < self.pos[0] or x_loc > self.pos[0] + self.button_n.get_width():
            #print('Button Normal X')
            self.highlighted = False
            return False

        if y_loc < self.pos[1] or y_loc > self.pos[1] + self.button_n.get_height():
            #print('Button Normal Y')
            self.highlighted = False
            return False

        #print('Button Highlighted')
        self.highlighted = True
        return True

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
        while len(self.send_q) > 0:
            try:
                self.sock.send(self.send_q.popleft())
            except socket.error as msg:
                print("Could not send, ", msg)

    def recieve(self):
        try:
            buffer = self.recv_buf + self.sock.recv(2048)
        except socket.error as msg:
            print("Could not receive, ", msg)
        if len(buffer) == 0:
            return

        self.recv_buf = ""
        split = string.split(buffer)
        if (buffer[-1] != "\n"):
            self.recv_buf = split[-1]
            del split[-1]

        for field in split:
            self.recv_q.append(field)

def color_menu(screen, name, clock, send_q):
    menu_width = 400
    menu_height = 350
    menu_surface = pygame.Surface((menu_width, menu_height))
    menu_surface.fill(colors['scores_border'])
    ok_button = GuiButton('ok', (470, 445))

    close = False
    while not close:
        menu_surface.fill(colors['scores_border'])
        pygame.draw.rect(menu_surface, colors['bg_menu'], [3, 3, menu_width - 6, menu_height - 6])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close = True
            elif event.type == pygame.KEYDOWN and (48 <= event.key <= 57 or 97 <= event.key <= 122 or event.key == pygame.K_BACKSPACE):
                print(event)
            elif event.type == pygame.MOUSEBUTTONDOWN and ok_button.test_mouse(event.pos):
                close = True
            elif event.type == pygame.MOUSEMOTION:
                ok_button.test_mouse(event.pos)

        for i in range(1, 9):
            index = str(i)
            n = i - 1

            col = n % 4
            row = n / 4

            x_pos = (col * 70 + col * 20) + 30
            y_pos = ((n / 4) * 90) + 110
            pygame.draw.rect(menu_surface, colors[index], [x_pos, y_pos, 70, 70])

        screen.blit(menu_surface, (200, 150))
        ok_button.draw(screen)

        # Render text box
        name_label = fonts['ui'].render('name:', True, colors['scores_border'])
        name_text = fonts['ui'].render(name, True, colors['white'])
        screen.blit(name_label, (230, 185))
        screen.blit(name_text, (230 + name_label.get_width() + 10, 185))

        pygame.display.update()
        clock.tick(10)

def test_mouse(pos, rect):
    x_loc = pos[0]
    y_loc = pos[1]

    if x_loc < rect[0] or x_loc > rect[0] + rect[2]:
        return False
    if y_loc < rect[1] or y_loc > rect[1] + rect[3]:
        return False

    return True


def game_loop(screen, send_q, recv_q):
    global quit
    #global lib_sans_small 
    #global lib_sans
    clock = pygame.time.Clock()

    # Set up play area surface
    bg_play = pygame.Color("black")
    screen.fill(bg_play)

    # Set up scores surface
    scores_surface = pygame.Surface((200, 600))
    bg_scores = pygame.Color("#575757")
    scores_surface.fill(bg_scores)
    score_x = 12

    # Set up font for scores
    #lib_sans = pygame.font.SysFont('Liberation Sans', 30)
    font_height = fonts['ui'].get_height()
    font_offset = font_height + 5

    # Set up scores header
    fonts['ui'].set_underline(True)
    scores_header = fonts['ui'].render("scores", True, colors['white'])
    fonts['ui'].set_underline(False)
    offset_scores_header = (200 - scores_header.get_width()) / 2

    #lib_sans_small = pygame.font.SysFont('Liberation Sans', 16)
    color_button = GuiButton('color', (650, 500))
    quit_button = GuiButton('quit', (650, 550))

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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if quit_button.test_mouse(event.pos):
                    quit = True
                elif color_button.test_mouse(event.pos):
                    color_menu(screen, players[my_id].player_char, clock, send_q)
                    color_button.test_mouse((0, 0))
            elif event.type == pygame.MOUSEMOTION:
                color_button.test_mouse(event.pos)
                quit_button.test_mouse(event.pos)

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
            scores_surface.blit(fonts['ui'].render(p.player_char, True, colors[str(i)]), (score_x, score_y))
            score = fonts['ui'].render(str(p.num_points), True, colors['white'])
            scores_surface.blit(score, (200 - score.get_width() - score_x, score_y))


            #update score y loc
            score_y = score_y + font_offset

        pygame.draw.line(scores_surface, colors['scores_border'], [0, 0], [0, 600], 5)
        scores_surface.blit(scores_header, (offset_scores_header, 5))
        screen.blit(scores_surface, (600, 0))
        color_button.draw(screen)
        quit_button.draw(screen)
        #screen.blit(color_button, (650, 500))
        # Refresh the screen
        pygame.display.update()
        clock.tick(15)


def main():
    global fonts

    # set up socket parameters
    port = 11000
    ip = "localhost"
    if args.port:
        port = args.port

    if args.ip:
        ip = args.ip

    # set up pygame
    pygame.init()
    fonts['ui'] = pygame.font.Font('resources/fonts/LiberationSans-Regular.ttf', 30)
    fonts['sm'] = pygame.font.Font('resources/fonts/LiberationSans-Regular.ttf', 16)

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
