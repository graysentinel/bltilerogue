import random
import objects
import idgen
import game_ai
import colors
from tcod import libtcodpy as tcod
import effects


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
        self.effects = []
        self.tiles = [[ 0 for y in range(self.height * 2) ]
                        for x in range(self.width * 4) ]
        self.tiles_explored = [[ 0 for y in range(self.height * 2) ]
                                 for x in range(self.width * 4) ]
        self.max_room_size = 10
        self.min_room_size = 4
        self.max_rooms = 30
        self.max_room_monsters = 3

        self.timer = 0
        self.cleanup_time = 100

        self.max_room_items = 2

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
            w = random.randint(self.min_room_size, self.max_room_size)
            h = random.randint(self.min_room_size, self.max_room_size)

            x = random.randint(0, self.width - w - 1)
            y = random.randint(0, self.height - h - 1)

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

                    if random.randint(0, 1):
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

        # debug light casting
        torch_room = random.choice(self.rooms)
        torch_x = random.randint(torch_room.x+1, torch_room.x2-1)
        torch_y = random.randint(torch_room.y+1, torch_room.y2-1)
        print(torch_x, torch_y)
        torchlight = objects.LightSource(radius=2, color=colors.lighter_yellow)
        torch = objects.GameObject('torch', torch_x, torch_y, 0xE200,
                                   light_source=torchlight, active=False)
        torch.current_map = self
        torch.light_source.cast_light()
        self.objects.append(torch)

        sword_item = objects.Item()
        sword_wpn = objects.Weapon(2, effects.sword_attack)
        sword = objects.GameObject('sword', player.x + 1, player.y + 1, 0xE251,
                                   item=sword_item, weapon=sword_wpn,
                                   active=False)
        sword.current_map = self
        self.objects.append(sword)

        bow_item = objects.Item()
        bow_wpn = objects.Weapon(2, effects.bow_attack, ranged=True, radius=5,
                                 ammo_icons={'n' : 0xE350, 's' : 0xE351,
                                             'w' : 0xE352, 'e' : 0xE353,
                                             'ne' : 0xE354, 'nw' : 0xE355,
                                             'se' : 0xE356, 'sw' : 0xE357},
                                 ammo_name='arrow')
        bow = objects.GameObject('bow', player.x - 1, player.y - 1, 0xE252,
                                 item=bow_item, weapon=bow_wpn, active=False)
        bow.current_map = self
        self.objects.append(bow)

        spear_item = objects.Item()
        spear_wpn = objects.Weapon(power=2,
                                   attack_function=effects.spear_attack,
                                   special=effects.push_back)
        spear = objects.GameObject('spear', player.x, player.y-1, 0xE253,
                                   item=spear_item, weapon=spear_wpn,
                                   active=False)
        spear.current_map = self
        self.objects.append(spear)

        axe_item = objects.Item()
        axe_wpn = objects.Weapon(power=2, attack_function=effects.axe_attack)
        axe = objects.GameObject('axe', player.x - 1, player.y + 1, 0xE250,
                                 item=axe_item, weapon=axe_wpn, active=False)
        axe.current_map = self
        self.objects.append(axe)

        lb_item = objects.Item()
        lb_spell = objects.SpellEffect(name='Lightning', spell_range=5,
                                       damage=15, render_frames=3,
                                       icons={'n' : 0xE370, 's' : 0xE370,
                                              'w' : 0XE371, 'e' : 0xE371,
                                              'ne' : 0xE372, 'sw': 0xE372,
                                              'nw' : 0xE373, 'se' : 0xE373,
                                              'hit' : 0xE374},
                                       charges=5,
                                       aoe_function=effects.lightning_bolt)
        lb_book = objects.GameObject('Book of Lightning Bolt', player.x + 1,
                                     player.y, 0xE360, item=lb_item,
                                     spell=lb_spell, active=False,
                                     update_func=objects.update_spell)
        lb_book.current_map = self
        self.objects.append(lb_book)

        fb_item = objects.Item()
        fb_spell = objects.SpellEffect(name='Fireball', spell_range=10,
                                       damage=10, render_frames=3,
                                       icons={'n' : 0xE380, 's' : 0xE381,
                                              'w' : 0xE382, 'e' : 0xE383,
                                              'ne' : 0xE384, 'nw' : 0xE385,
                                              'se' : 0xE386, 'sw' : 0xE387,
                                              'hit' : 0xE388},
                                       charges=5,
                                       aoe_function=effects.fireball)
        fb_book = objects.GameObject('Book of Fireball', player.x-1, player.y,
                                     0xE361, item=fb_item, spell=fb_spell,
                                     active=False,
                                     update_func=objects.update_spell)

        fb_book.current_map = self
        self.objects.append(fb_book)

        self.assign_object_ids()

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

    def terrain_blocked_at(self, x, y):
        for t in terrain_types:
            if self.tiles[x][y] == t.terrain_id:
                return t.blocks

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

    def out_of_bounds(self, x, y):
        if (x < 0 or x > self.width) or (y < 0 or y > self.height):
            return True

        return False

    def place_objects(self, room):

        num_monsters = random.randint(0, self.max_room_monsters)
        monster_counter = 0

        for i in range(num_monsters):
            x = random.randint(room.x, room.x2)
            y = random.randint(room.y, room.y2)

            if not self.is_blocked_at(x, y):
                if random.randint(0, 100) < 80:
                    ai_component = game_ai.BasicMonster(20)
                    monster_fighter = objects.Fighter(hp=10, defense=0, power=3,
                                      recharge=20,
                                      death_function=ai_component.monster_death)
                    monster = objects.GameObject('orc', x, y,
                                                 0xE101, blocks=True,
                                                 fighter=monster_fighter,
                                                 ai=ai_component,
                                             update_func=objects.update_monster)
                else:
                    ai_component = game_ai.BasicMonster(30)
                    monster_fighter = objects.Fighter(hp=16, defense=1, power=4,
                                      recharge=30,
                                      death_function=ai_component.monster_death)
                    monster = objects.GameObject('troll', x, y, 0xE100,
                                                  blocks=True,
                                                  fighter=monster_fighter,
                                                  ai=ai_component,
                                             update_func=objects.update_monster)

                monster.current_map = self
                self.objects.append(monster)

        num_items = random.randint(0, self.max_room_items)

        for i in range(num_items):
            x = random.randint(room.x+1, room.x2-1)
            y = random.randint(room.y+1, room.y2-1)

            if not self.is_blocked_at(x, y):
                item_component = objects.Item(use_function=effects.cast_heal)
                item = objects.GameObject('healing potion', x, y, 0xE201,
                                          item=item_component, active=False)

                self.objects.append(item)
                item.current_map = self
                item.send_to_back()


    def assign_object_ids(self):
        pool = idgen.generate_id_pool(len(self.objects))

        for obj in self.objects:
            if obj.name != 'player':
                obj.object_id = pool.pop()

    def cleanup(self):
        for effect in self.effects:
            if not effect.active:
                self.effects.remove(effect)

    def update(self):
        self.timer += 1
        if self.timer == self.cleanup_time:
            self.cleanup()
            self.timer = 0


class DungeonMapBSP(DungeonMap):

    def __init__(self, width, height, depth=10, min_size=5, full_rooms=False):
        DungeonMap.__init__(self, width, height)
        # self.width = width
        # self.height = height
        self.depth = depth
        self.min_size = min_size
        self.full_rooms = full_rooms

        self.tiles = [[ 0 for y in range(self.height * 2) ]
                        for x in range(self.width * 4) ]

        self.tiles_explored = [[ 0 for y in range(self.height * 2) ]
                                 for x in range(self.width * 4) ]

        self.rooms = []
        self.room_objects = []
        self.objects = []

    def make_map(self, player):
        bsp = tcod.bsp_new_with_size(0, 0, self.width, self.height)

        tcod.bsp_split_recursive(bsp, 0, self.depth, self.min_size+1,
                                 self.min_size+1, 1.5, 1.5)

        tcod.bsp_traverse_inverted_level_order(bsp, self.traverse_node)

        # Block for adding stairs later

        player_room = random.choice(self.rooms)
        self.rooms.remove(player_room)

        player.x = player_room[0]
        player.y = player_room[1]
        # print("Player Position: ({}, {})".format(player.x, player.y))

        for room in self.room_objects:
            self.place_objects(room)

    def traverse_node(self, node, dat):
        if tcod.bsp_is_leaf(node):
            minx = node.x + 1
            maxx = node.x + node.w - 1
            miny = node.y + 1
            maxy = node.y + node.h - 1

            if maxx == self.width - 1:
                maxx -= 1
            if maxy == self.height - 1:
                maxy -= 1

            if self.full_rooms == False:
                minx = tcod.random_get_int(None, minx, maxx - self.min_size+1)
                miny = tcod.random_get_int(None, miny, maxy - self.min_size+1)
                maxx = tcod.random_get_int(None, minx + self.min_size - 2, maxx)
                maxy = tcod.random_get_int(None, miny + self.min_size - 2, maxy)

            node.x = minx
            node.y = miny
            node.w = maxx-minx + 1
            node.h = maxy-miny + 1

            for x in range(minx, maxx + 1):
                for y in range(miny, maxy + 1):
                    self.tiles[x][y] = 1

            self.rooms.append(((minx + maxx) // 2, (miny + maxy) // 2))
            new_room = Room(node.x, node.y, node.w, node.h)
            self.room_objects.append(new_room)

        else:
            left = tcod.bsp_left(node)
            right = tcod.bsp_right(node)
            node.x = min(left.x, right.x)
            node.y = min(left.y, right.y)
            node.w = max(left.x + left.w, right.x + right.w) - node.x
            node.h = max(left.y + left.h, right.y + right.h) - node.y
            if node.horizontal:
                if (left.x + left.w - 1 < right.x or
                    right.x + right.w - 1 < left.x):
                    x1 = tcod.random_get_int(None, left.x, left.x + left.w - 1)
                    x2 = tcod.random_get_int(None, right.x, right.x +
                                             right.w - 1)
                    y = tcod.random_get_int(None, left.y + left.h, right.y)
                    self.vline_up(x1, y - 1)
                    self.hline(x1, y, x2)
                    self.vline_down(x2, y + 1)

                else:
                    minx = max(left.x, right.x)
                    maxx = min(left.x + left.w - 1, right.x + right.w - 1)
                    x = tcod.random_get_int(None, minx, maxx)
                    self.vline_down(x, right.y)
                    self.vline_up(x, right.y - 1)

            else:
                if ( left.y + left.h - 1 < right.y or
                    right.y + right.h - 1 < left.y ):
                    y1 = tcod.random_get_int(None, left.y, left.y + left.h - 1)
                    y2 = tcod.random_get_int(None, right.y,
                                             right.y + right.h - 1)
                    x = tcod.random_get_int(None, left.x + left.w, right.x)
                    self.hline_left(x - 1, y1)
                    self.vline(x, y1, y2)
                    self.hline_right(x + 1, y2)
                else:
                    miny = max(left.y, right.y)
                    maxy = min(left.y + left.h - 1, right.y + right.h - 1)
                    y = tcod.random_get_int(None, miny, maxy)
                    self.hline_left(right.x - 1, y)
                    self.hline_right(right.x, y)

        return True

    def vline(self, x, y1, y2):
        if y1 > y2:
            y1, y2 = y2, y1

        for y in range(y1, y2+1):
            self.tiles[x][y] = 1

    def vline_up(self, x, y):
        while y >= 0 and self.tiles[x][y] == 0:
            self.tiles[x][y] = 1
            y -= 1

    def vline_down(self, x, y):
        while y < self.height and self.tiles[x][y] == 0:
            self.tiles[x][y] = 1
            y += 1

    def hline(self, x1, y, x2):
        if x1 > x2:
            x1, x2 = x2, x1

        for x in range(x1, x2+1):
            self.tiles[x][y] = 1

    def hline_left(self, x, y):
        while x >= 0 and self.tiles[x][y] == 0:
            self.tiles[x][y] = 1
            x -= 1

    def hline_right(self, x, y):
        while x < self.width and self.tiles[x][y] == 0:
            self.tiles[x][y] = 1
            x += 1
