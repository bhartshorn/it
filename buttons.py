import pygame

class ColorButton():
    def __init__(self, color, pos):
        self.color = color
        self.pos = pos
        self.highlighted = False
        self.clicked = False
        self.cube = pygame.Surface((70, 70))
        self.cube.fill(self.color)

        self.cube_hl = pygame.Surface((70, 70))
        self.cube_hl.fill(pygame.Color('white'))
        pygame.draw.rect(self.cube_hl, self.color, [2, 2, 66, 66])

    def draw(self, surface):
        if self.highlighted or self.clicked:
            surface.blit(self.cube_hl, (self.pos[0], self.pos[1]))
        else:
            surface.blit(self.cube, (self.pos[0], self.pos[1]))


    def test_mouse(self, pos):
        x_loc = pos[0]
        y_loc = pos[1]

        if x_loc < self.pos[0] or x_loc > self.pos[0] + 70:
            #print('Button Normal X')
            self.highlighted = False
            return False

        if y_loc < self.pos[1] or y_loc > self.pos[1] + 70:
            #print('Button Normal Y')
            self.highlighted = False
            return False

        #print('Button Highlighted')
        self.highlighted = True
        return True

    def click(self, pos):
        if self.test_mouse(pos):
            self.clicked = True
            return True

    def unclick(self):
        self.clicked = False

class GuiButton():
    def __init__(self, label, font, colors, pos):
        self.label = label
        self.pos = pos
        self.font = font
        self.highlighted = False

        self.text_n = font.render(label, 1, colors['scores_border'])
        self.button_n = pygame.Surface((100, self.text_n.get_height() + 16))
        self.button_n.fill(colors['scores_border'])
        pygame.draw.rect(self.button_n, colors['bg_menu'], [2, 2, self.button_n.get_width() - 4, self.button_n.get_height() - 4])

        self.button_n.blit(self.text_n, ((100 - self.text_n.get_width()) / 2, 8))

        self.text_h = font.render(label, 1, colors['white'])
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
