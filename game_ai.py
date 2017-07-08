import objects
import random
import time

class BasicMonster:
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
