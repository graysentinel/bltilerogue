import objects
import random
import time
import log
import colors
from tcod import libtcodpy as tcod

class BasicMonster:
    def __init__(self, turn_timer, active_flag=False):
        self.turn_timer = turn_timer
        self.active = active_flag
        self.turns = 0

    def take_turn(self):
        monster = self.owner

        for obj in monster.current_map.objects:
            if obj.name == 'player':
                p = obj

        if not self.active:
            if monster.distance_to(p) < 10:
                self.active = True
        else:
            if self.turns < self.turn_timer:
                self.turns += 1
            else:
                if monster.distance_to(p) > 10:
                    self.active = False
                else:
                    if monster.distance_to(p) >= 2:
                        self.move_astar(p)
                    elif p.fighter.hp > 0:
                        monster.fighter.attack(p)

                    self.turns = 0

    def move_astar(self, target):
        monster = self.owner
        fov = tcod.map_new(monster.current_map.width,
                           monster.current_map.height)

        for y1 in range(monster.current_map.height):
            for x1 in range(monster.current_map.width):
                tcod.map_set_properties(fov, x1, y1,
                not monster.current_map.sight_blocked_at(x1, y1),
                not monster.current_map.is_blocked_at(x1, y1))

        monster_path = tcod.path_new_using_map(fov, 1.41)
        tcod.path_compute(monster_path, monster.x, monster.y, target.x,
                          target.y)

        if not (tcod.path_is_empty(monster_path) and
            tcod.path_size(monster_path) < 25):

            x, y = tcod.path_walk(monster_path, True)
            if not monster.current_map.is_blocked_at(x, y):
                monster.x = x
                monster.y = y
                # print("{} Position: {}, {}".format(monster.name, x, y))

        else:
            x, y = monster.move_towards(target.x, target.y)
            if not monster.current_map.is_blocked_at(x, y):
                monster.x, monster.y = x, y
                # print("{} Position: {}, {}".format(monster.name, x, y))

        tcod.path_delete(monster_path)

    def monster_death(self, monster):
        log.message(monster.name.capitalize() + ' dies!', colors.turquoise)
        monster.icon = 0xE150
        monster.blocks = False
        monster.fighter = None
        monster.ai = None
        monster.active = False
        monster.name = 'Remains of ' + monster.name
        monster.send_to_back()

    def update(self):
        self.take_turn()



class ConfusedMonster:
    def __init__(self, turn_timer):
        self.turn_timer = turn_timer
        self.turns = 0

    def take_turn(self):
        monster = self.owner
        if self.turns < self.turn_timer:
            self.turns += 1
        else:
            x, y = monster.move(random.choice(objects.directions))
            if not monster.current_map.is_blocked_at(x, y):
                monster.x, monster.y = x, y
                self.turns = 0
