from bearlibterminal import terminal
import math
import log
import colors

class GameObject:
    def __init__(self, name, x, y, icon, blocks=False, fighter=None, ai=None):
        self.name = name
        self.x = x
        self.y = y
        self.icon = icon
        self.blocks = blocks

        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self

        self.ai = ai
        if self.ai:
            self.ai.owner = self

        self.object_id = None

    def draw(self, camera):
        x, y = camera.to_camera_coordinates(self.x, self.y)
        terminal.put(x*4, y*2, self.icon)

    def clear(self, camera):
        x, y = camera.to_camera_coordinates(self.x, self.y)
        terminal.put(x*4, y*2, ' ')

    def move(self, direction):
        tgt_x = self.x + direction.goal_x
        tgt_y = self.y + direction.goal_y

        return(tgt_x, tgt_y)

    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))

        return(self.x + dx, self.y + dy)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    @property
    def current_position(self):
        return "(" + str(self.x) + "," + str(self.y) + ")"


class Camera:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.x2 = self.x + self.width
        self.y2 = self.y + self.height

    def move(self, direction):
        self.x += direction.goal_x
        self.y += direction.goal_y
        # print("Camera Top-Left: ({}, {})".format(self.x, self.y))

    def center_view(self, target):
        self.x = target.x - (self.width // 2)
        self.y = target.y - (self.height // 2)
        # print("Camera Top-Left: ({}, {})".format(self.x, self.y))

    def in_fov(self, x, y):
        x2 = self.x + self.width
        y2 = self.y + self.height

        if x in range(self.x, self.x) and y in range(self.y, self.y2):
            return True

        return False

    def offset(self, x, y):
        return x + self.x, y + self.y

    def to_camera_coordinates(self, x, y):
        (x, y) = (x - self.x, y - self.y)

        return x, y

    @property
    def center(self):
        return self.width // 2, self.height // 2


class Direction:
    def __init__(self, goal_x, goal_y):
        self.goal_x = goal_x
        self.goal_y = goal_y

north = Direction(0, -1)
south = Direction(0, 1)
east = Direction(1, 0)
west = Direction(-1, 0)
northeast = Direction(1, -1)
northwest = Direction(-1, -1)
southeast = Direction(1, 1)
southwest = Direction(-1, 1)

directions = [north, south, east, west, northeast, northwest, southeast,
              southwest]


class Fighter:
    def __init__(self, hp, defense, power, recharge, death_function=None):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.recharge_timer = recharge
        self.death_function = death_function

        self.power_meter = 100

    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage

        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)

    def attack(self, target):
        damage = math.floor((self.power * (self.power_meter / 100) -
                  target.fighter.defense))

        if damage > 0:
            log.message(self.owner.name.capitalize() + ' attacks ' +
                        target.name + ' for ' + str(damage) + ' hit points!',
                        colors.orange)
            target.fighter.take_damage(damage)
        else:
            log.message(self.owner.name.capitalize() + ' attacks ' + 
                        target.name + ' but it has no effect!', colors.red)

        self.power_meter = 0

    def recharge(self):
        if self.power_meter < 100:
            self.power_meter += math.floor(100/self.recharge_timer)
