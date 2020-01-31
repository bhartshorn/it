import socket
import select
import threading
import argparse
import pygame
import buttons
from pygame import gfxdraw
from player import Player
from collections import deque
from pygame_functions import *

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, help="port number to connect to")
parser.add_argument("-i", "--ip", help="ip address to connect to")
args = parser.parse_args()
quit = False
my_id = 1

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


class flashingCursor():
    def __init__(self, font, color, flashrate, pos):
        self.pos = pos
        self.font = font
        self.color = color

        self.flashrate = flashrate
        self.halfrate = self.flashrate / 2
        self.frame = 0

        self.cursor_text = self.font.render('|', 1, self.color)

    def draw(self, surface):
        if self.frame < self.halfrate:
            surface.blit(self.cursor_text, (self.pos[0], self.pos[1]))

        self.frame = (self.frame + 1) % self.flashrate

    def move(self, newpos):
        self.pos = newpos


class NetworkThread(threading.Thread):
    recv_buf = b''

    def __init__(self, sock, send_q, recv_q):
        threading.Thread.__init__(self)
        self.sock = sock
        self.send_q = send_q
        self.recv_q = recv_q

def run(self):
        global quit
        while not quit:
            readable, w, e = select.select([self.sock], [], [], 10)
            if len(readable) > 0:
                self.recieve()

            if len(self.send_q) > 0:
                self.send()

    def send(self):
        while len(self.send_q) > 0:
            try:
                self.sock.send(self.send_q.popleft().encode())
            except socket.error as msg:
                print("Could not send, ", msg)

    def recieve(self):
        try:
            buffer = self.recv_buf.decode() + self.sock.recv(2048).decode()
        except socket.error as msg:
            print("Could not receive, ", msg)
        if len(buffer) == 0:
            return

        self.recv_buf = b''
        split = buffer.split()
        if (buffer[-1] != "\n"):
            self.recv_buf = split[-1]
            del split[-1]

        for field in split:
            self.recv_q.append(field)
        # print(self.recv_q)


def color_menu(screen, name, color_index, clock, send_q):
    # bg = screen.copy()
    bg = pygame.transform.smoothscale(screen, (200, 150))
    bg = pygame.transform.smoothscale(bg, (800, 600))

    menu_width = 400
    menu_height = 350
    menu_surface = pygame.Surface((menu_width, menu_height))
    menu_surface.fill(colors['scores_border'])

    save_button = buttons.GuiButton('save', fonts['sm'], colors, (470, 445))
    color_buttons = []
    font_height = fonts['sm'].get_height()

    text_box = pygame.Surface((200, font_height + 24))
    text_box.fill(colors['white'])
    pygame.draw.rect(text_box, colors['bg_menu'], [3, 3, 194, font_height + 18])

    name_label = fonts['ui'].render('name:', True, colors['scores_border'])
    name_label_width = name_label.get_width()

    cursor = flashingCursor(fonts['ui'], colors['white'], 10, (0, 0))

    for i in range(1, 9):
        index = str(i)
        n = i - 1

        col = n % 4
        row = n // 4

        x_pos = (col * 90) + 230
        y_pos = (row * 90) + 260
        color_buttons.append(buttons.ColorButton(colors[index], (x_pos, y_pos)))

    color_buttons[color_index - 1].clicked = True

    close = False
    while not close:
        menu_surface.fill(colors['scores_border'])
        pygame.draw.rect(menu_surface, colors['bg_menu'], [3, 3, menu_width - 6, menu_height - 6])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close = True
            elif event.type == pygame.KEYDOWN:
                if (48 <= event.key <= 57 or 97 <= event.key <= 122) and len(name) < 7:
                    name = name + pygame.key.name(event.key)
                elif event.key == pygame.K_BACKSPACE and len(name) >= 0:
                    name = name[:-1]
                elif event.key == pygame.K_RETURN:
                    send_q.append("c:{}:{}:{}\n".format(my_id, name, color_index))
                    close = True
                elif event.key == pygame.K_ESCAPE:
                    close = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if save_button.test_mouse(event.pos):
                    send_q.append("c:{}:{}:{}\n".format(my_id, name, color_index))
                    close = True
                for index, button in enumerate(color_buttons, start=1):
                    if button.click(event.pos):
                        color_index = index
                        for unclick in color_buttons:
                            if button is not unclick:
                                unclick.unclick()
            elif event.type == pygame.MOUSEMOTION:
                save_button.test_mouse(event.pos)
                for button in color_buttons:
                    button.test_mouse(event.pos)

        screen.blit(bg, (0, 0))
        screen.blit(menu_surface, (200, 150))
        save_button.draw(screen)

        for button in color_buttons:
            button.draw(screen)

        # Render text box
        name_text = fonts['ui'].render(name, True, colors['white'])

        cursor.move((230 + name_label_width + name_text.get_width() + 14, 185))

        screen.blit(name_label, (230, 185))
        screen.blit(text_box, (230 + name_label_width + 8, 183))
        screen.blit(name_text, (230 + name_label_width + 14, 185))
        cursor.draw(screen)

        pygame.display.update()
        clock.tick(10)


def game_loop(screen, send_q, recv_q):
    global quit
    # global lib_sans_small 
    # global lib_sans
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
    #l ib_sans = pygame.font.SysFont('Liberation Sans', 30)
    font_height = fonts['ui'].get_height()
    font_offset = font_height + 5

    # Set up scores header
    fonts['ui'].set_underline(True)
    scores_header = fonts['ui'].render("scores", True, colors['scores_border'])
    fonts['ui'].set_underline(False)
    offset_scores_header = (200 - scores_header.get_width()) / 2

    # lib_sans_small = pygame.font.SysFont('Liberation Sans', 16)
    color_button = buttons.GuiButton('name/color', fonts['sm'], colors, (650, 500))
    quit_button = buttons.GuiButton('quit', fonts['sm'], colors, (650, 550))

    # Set up circle parameters
    circle_radius = 10
    circle_radius_inner = 5

    # Game state
    players = {}
    global my_id

    while not quit:
        command = ""

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_q):
                send_q.append("q:{}\n".format(my_id))
                quit = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if quit_button.test_mouse(event.pos):
                    quit = True
                elif color_button.test_mouse(event.pos):
                    color_menu(screen, players[my_id].player_char, players[my_id].player_color, clock, send_q)
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
            command = recv_q.popleft().split(":")
            if command[0] == "q":
                quit = True
            elif command[0] == "i":
                my_id = int(command[1])
            elif command[0] == "p" and len(command) >= 2:
                p_id = int(command[1])
                if int(p_id) not in players:
                    players[p_id] = Player(p_id)

                players[p_id].parse_network(command)

        score_y = font_offset
        screen.fill(bg_play)
        scores_surface.fill(bg_scores)

        for i, p in players.items():
            # Draw player on screen
            if (p.has_ball):
                draw_x = (p.loc_x * circle_radius)
                draw_y = (p.loc_y * circle_radius)
                pygame.draw.rect(screen, colors[str(p.player_color)], [draw_x, draw_y, circle_radius * 2, circle_radius * 2])
                pygame.draw.rect(screen,
                        bg_play,
                        [draw_x + (circle_radius / 2),
                            draw_y + (circle_radius / 2),
                            circle_radius,
                            circle_radius])
            else:
                draw_x = (p.loc_x * circle_radius) + circle_radius
                draw_y = (p.loc_y * circle_radius) + circle_radius

                # Yeah... this is harder than it needs to be!
                gfxdraw.aacircle(screen, draw_x, draw_y, circle_radius, colors[str(p.player_color)])
                gfxdraw.filled_circle(screen, draw_x, draw_y, circle_radius, colors[str(p.player_color)])
                gfxdraw.aacircle(screen, draw_x, draw_y, circle_radius_inner, bg_play)
                gfxdraw.filled_circle(screen, draw_x, draw_y, circle_radius_inner, bg_play)

            # Draw player's score
            scores_surface.blit(fonts['ui'].render(p.player_char, True, colors[str(p.player_color)]), (score_x, score_y))
            score = fonts['ui'].render(str(p.num_points), True, colors['white'])
            scores_surface.blit(score, (200 - score.get_width() - score_x, score_y))

            # update score y loc
            score_y = score_y + font_offset

        pygame.draw.line(scores_surface, colors['scores_border'], [0, 0], [0, 600], 5)
        scores_surface.blit(scores_header, (offset_scores_header, 5))
        screen.blit(scores_surface, (600, 0))
        color_button.draw(screen)
        quit_button.draw(screen)
        # screen.blit(color_button, (650, 500))
        # Refresh the screen
        pygame.display.update()
        clock.tick(15)


def port_prompt():
    screen_width = 450
    screen_height = 235
    screen = screenSize(screen_width, screen_height)
    setBackgroundColour(colors["bg_menu"])

    pygame.draw.rect(screen, (211, 211, 211), [0, 0, screen_width - 1, screen_height - 1], 2)
    intro_label = makeLabel("Welcome to \"IT\"", 40, 19, 22, "white", "LiberationsSansRegular")
    showLabel(intro_label)

    ip_label = makeLabel("Server IP:", 40, 19, 75, "white", "LiberationsSansRegular")
    showLabel(ip_label)

    port_label = makeLabel("Port:", 40, 19, 120, "white", "LiberationsSansRegular")
    showLabel(port_label)

    ip_box = makeTextBox(195, 70, screen_width / 2, 0, "localhost", 15, 40, False)
    port_box = makeTextBox(195, 125, screen_width / 2, 0, "11000", 10, 40)

    showTextBox(ip_box)
    showTextBox(port_box)

    connect_button = newSprite("connect_button.png")
    connect_button.addImage("connect_button2.png")
    connect_button.move(315, 190)
    showSprite(connect_button)

    #set default values
    ip_entry = str(ip_box.text)
    port_entry = int(port_box.text)

    while True:
        ip_entry, key = ip_box.update()
        if key == pygame.MOUSEBUTTONDOWN:
            connect_button.changeImage(1)
            return str(ip_entry), int(port_entry)
        port_entry, key = port_box.update()
        if key == pygame.K_RETURN or key == pygame.MOUSEBUTTONDOWN:
            connect_button.changeImage(1)
            showSprite(connect_button)
            return str(ip_entry), int(port_entry)


def main():
    global fonts

    # set up socket parameters
    port = 11000
    ip = "localhost"

    if args.port:
        port = args.port

    if args.ip:
        ip = args.ip
    else:
        ip, port = port_prompt()

    # set up pygame
    pygame.init()

    fonts['ui'] = pygame.font.Font('resources/fonts/LiberationSans-Regular.ttf', 30)
    fonts['sm'] = pygame.font.Font('resources/fonts/LiberationSans-Regular.ttf', 16)

    game_window = pygame.display.set_mode((800, 600))

    # set up the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # TODO: Attempt connecting on higher ports automatically -- The Unix Way?
    sock.connect((ip, port))

    send_q = deque()
    recv_q = deque()
    network_thread = NetworkThread(sock, send_q, recv_q)
    network_thread.start()

    game_loop(game_window, send_q, recv_q)

    sock.close()


if __name__ == "__main__":
    main()
