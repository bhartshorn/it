import time

AREA_WIDTH = 59
AREA_HEIGHT = 59

class Player:
    player_id = -1
    has_ball = False
    lost_ball_time = 0
    num_points = 0
    player_char = "0"
    player_color = 1
    loc_x = 0
    loc_y = 0
    last_updated = -1

    #client_socket = 

    def __init__ (self, id):
        self.player_id = id
        self.player_char = str(id)

    def move(self, input):
        #if (len(command) != 3 or command[2] == "" or command[1] != self.player_id):
            #return -1

        #print("Player " + input[1] + " wants to move " + input[2])
        if input[2] == "u":
            self.loc_y = (self.loc_y - 1) % AREA_HEIGHT
        elif input[2] == "d":
            self.loc_y = (self.loc_y + 1) % AREA_HEIGHT
        elif input[2] == "r":
            self.loc_x = (self.loc_x + 1) % AREA_WIDTH
        elif input[2] == "l":
            self.loc_x = (self.loc_x - 1) % AREA_WIDTH

        self.last_dir = input[2]

    def parse_network(self, command):
        # Command comes in as an array
        # Confirm array is correctly sized
        if len(command) == 8 and command[7] != "" and int(command[1]) == self.player_id:
            self.loc_x = int(command[2])
            self.loc_y = int(command[3])
            self.player_char = command[4]
            self.player_color = int(command[5])
            self.num_points = int(command[7])
            if command[6] == "0":
                self.has_ball = False
            elif command[6] == "1":
                self.has_ball = True
        else:
            print("Error parsing network string")

    def to_network(self):
        network_string = "p:{}:{}:{}:{}:{}:{}:{}\n".format(self.player_id,
                                                        self.loc_x,
                                                        self.loc_y,
                                                        self.player_char,
                                                        self.player_color,
                                                        self.has_ball_char(),
                                                        int(self.num_points))
        return network_string

    def take_ball(self):
        if self.has_ball:
            self.lost_ball_time = time.time()
            self.has_ball = False
            return True
        return False

    def give_ball(self):
        if (not self.has_ball) and (time.time() - self.lost_ball_time > 1):
            self.has_ball = True
            return True
        return False

    def has_ball_char(self):
        if not self.has_ball:
            return 0
        return 1


