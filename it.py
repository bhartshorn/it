import pygame
from pgu import gui

pygame.init()

#how to set colors
#pygame.Color("red")

#initialize the dialog
app = gui.Desktop()
app.connect(gui.QUIT,app.quit,None)


def onchange(value):
    print('-----------')
    print(ip_address_value.value)
    print(port_text_area.value)
    print(value)
    #for k, v in value.value.items():
    #    print(k, v)
    app.quit()


# open a new text input field
server_dialog = gui.Table()

server_dialog.tr()
server_dialog.td(gui.Label("IP Address"), colspan=4, align=-1)
ip_address_value = gui.Input(value="", width=190)
server_dialog.td(ip_address_value, colspan=4)

server_dialog.tr()
server_dialog.td(gui.Label("Port"), colspan=4, align=-1)
port_text_area = gui.Input(value="5000", width=190)
server_dialog.td(port_text_area, colspan=4)

server_dialog.tr()
e = gui.Button("Okay")
e.connect(gui.CLICK, onchange, server_dialog)
server_dialog.td(e)
##

e = gui.Button("Cancel")
e.connect(gui.CLICK, app.quit, None)
server_dialog.td(e)

app.run(server_dialog)
