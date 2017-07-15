import objects
import random
import time
import log
import colors

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
                        x, y = monster.move_towards(p.x, p.y)
                        if not monster.current_map.is_blocked_at(x, y):
                            monster.x, monster.y = x, y
                    elif p.fighter.hp > 0:
                        monster.fighter.attack(p)

                    self.turns = 0

    def monster_death(self, monster):
        log.message(monster.name.capitalize() + ' dies!', colors.turquoise)
        monster.icon = 0xE150
        monster.blocks = False
        monster.fighter = None
        monster.ai = None
        monster.name = 'Remains of ' + monster.name



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
