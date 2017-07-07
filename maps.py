from random import randint
import objects

'''
tile_types = {0: 'blank', 50: 'rock', 51: 'light_floor',
              52: 'dark_floor',53: 'bright_floor', 54: 'marble_floor',
              55: 'dark_marble_floor', 56: 'bright_marble_floor',
              60: 'dark_wall', 61: 'light_wall', 62: 'bright_wall'}
'''

class Terrain:
    def __init__(self, terrain_id, name, icon_seen, icon_unseen, blocks,
                 blocks_sight = None):
        self.terrain_id = terrain_id
        self.name = name
        self.icon_seen = icon_seen
        self.icon_unseen = icon_unseen
        self.blocks = blocks

        if blocks_sight is None: blocks_sight = blocks
        self.blocks_sight = blocks_sight

terrain_types = [Terrain(0, 'rock', 0xE060, 0xE061, True),
                 Terrain(1, 'floor', 0xE053, 0xE052, False),
                 Terrain(2, 'wall', 0xE062, 0xE060, True),
                 Terrain(3, 'door_closed', 0xE070, 0xE070, False, True)]

class Room:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.x2 = x + width
        self.y2 = y + height
        self.width = width
        self.height = height

        self.north_wall = []
        self.south_wall = []
        self.east_wall = []
        self.west_wall = []

        self.walls = [self.north_wall, self.south_wall, self.east_wall,
                      self.west_wall]

        self.floor = []

    def get_walls(self):
        # north wall
        for x in range(self.x, self.x + self.width):
            coord = (x, self.y)
            self.north_wall.append(coord)
        #south wall
        for x in range(self.x, self.x + (self.width + 1)):
            coord = (x, self.y+self.height)
            self.south_wall.append(coord)
        #west wall
        for y in range(self.y, self.y + self.height):
            coord = (self.x, y)
            self.west_wall.append(coord)
        #east wall
        for y in range(self.y, self.y + (self.height + 1)):
            coord = (self.x + self.width, y)
            self.east_wall.append(coord)
        #floor
        for y in range(self.y + 1, self.y + self.height):
            for x in range(self.x + 1, self.x + (self.width)):
                coord = (x, y)
                self.floor.append(coord)

    def center(self):
        ctr_x = (self.x + self.x2) // 2
        ctr_y = (self.y + self.y2) // 2
        return (ctr_x, ctr_y)

    def intersect(self, other):
        return (self.x <= other.x2 and self.x2 >= other.x and
                self.y <= other.y2 and self.y >- other.y)


class DungeonMap:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.objects = []
        self.tiles = [[ 0 for y in range(self.height) ]
                        for x in range(self.width * 2) ]
        self.tiles_explored = [[ 0 for y in range(self.height) ]
                                 for x in range(self.width * 2) ]
        self.max_room_size = 10
        self.min_room_size = 4
        self.max_rooms = 30
        self.max_room_monsters = 3

        self.rooms = []

        self.default_torch_radius = 5
        self.fov_recompute = True

    def draw_room(self, room):
        for x, y in room.floor:
            self.tiles[x][y] = 1

    def make_test_map(self, player):
        room = Room(7, 8, 4, 5)
        room.get_walls()
        self.draw_room(room)

        room2 = Room(17, 8, 5, 6)
        room2.get_walls()
        self.draw_room(room2)

        self.create_h_tunnel(room.x2, room2.x, 11)

        player.x, player.y = room.center()

    def make_map(self, player):
        num_rooms = 0

        for r in range(self.max_rooms):
            w = randint(self.min_room_size, self.max_room_size)
            h = randint(self.min_room_size, self.max_room_size)

            x = randint(0, self.width - w - 1)
            y = randint(0, self.height - h - 1)

            new_room = Room(x, y, w, h)
            failed = False

            for other_room in self.rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break

            if not failed:
                new_room.get_walls()
                self.draw_room(new_room)
                (new_x, new_y) = new_room.center()

                if num_rooms == 0:
                    player.x = new_x
                    player.y = new_y
                else:
                    (prev_x, prev_y) = self.rooms[num_rooms-1].center()

                    if randint(0, 1):
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)

                #for wall in new_room.walls:
                    #for x, y in wall:
                        #self.tiles[x][y] = 2

                self.rooms.append(new_room)
                self.place_objects(new_room)
                num_rooms += 1


    def create_h_tunnel(self, x1, x2, y):
        #self.tiles[x1][y] = 3
        #if self.tiles[x2][y] == 2:
        #    self.tiles[x2][y] = 3

        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y] = 1
            #self.tiles[x][y-1] = 2
            #self.tiles[x][y+1] = 2

    def create_v_tunnel(self, y1, y2, x):
        #self.tiles[x][y1] = 3
        #if self.tiles[x][y2] == 2:
        #    self.tiles[x][y2] = 3

        for y in range(min(y1, y2) + 1, max(y1, y2) + 1):
            self.tiles[x][y] = 1
            #self.tiles[x+1][y] = 2
            #self.tiles[x-1][y] = 2

    def is_blocked_at(self, x, y):
        for t in terrain_types:
            if self.tiles[x][y] == t.terrain_id:
                return t.blocks
            else:
                for obj in self.objects:
                    if obj.blocks and obj.x == x and obj.y == y:
                        return True

        return False

    def sight_blocked_at(self, x, y):
        for t in terrain_types:
            if self.tiles[x][y] == t.terrain_id:
                return t.blocks_sight

    def terrain_type_at(self, x, y):
        for t in terrain_types:
            if self.tiles[x][y] == t.terrain_id:
                return t.name

    def is_visible_tile(self, x, y):
        if x >= self.width or x < 0:
            return False
        elif y >= self.height or y < 0:
            return False
        elif self.is_blocked_at(x, y):
            return False
        elif self.sight_blocked_at(x, y):
            return False
        else:
            return True

    def place_objects(self, room):

        num_monsters = randint(0, self.max_room_monsters)
        print(num_monsters)

        for i in range(num_monsters):
            x = randint(room.x, room.x2)
            y = randint(room.y, room.y2)
            print('(' + str(x) + ',' + str(y) + ')')

            if not self.is_blocked_at(x, y):
                if randint(0, 100) < 80:
                    monster = objects.GameObject('orc', x, y, 0xE101,
                                                 blocks=True)
                else:
                    monster = objects.GameObject('troll', x, y, 0xE100,
                                                 blocks=True)

                self.objects.append(monster)
