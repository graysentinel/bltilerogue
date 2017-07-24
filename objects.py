from bearlibterminal import terminal
import math
import log
import colors
import raycast

class GameObject:
    def __init__(self, name, x, y, icon, blocks=False, fighter=None, ai=None,
                 light_source=None, item=None, weapon=None):
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

        self.light_source = light_source
        if self.light_source:
            self.light_source.owner = self

        self.item = item
        if self.item:
            self.item.owner = self

        self.weapon = weapon
        if self.weapon:
            self.weapon.owner = self

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

    def distance_to_square(self, x, y):
        dx = x - self.x
        dy = y - self.y
        return math.sqrt(dx ** 2 + dy ** 2)

    def send_to_back(self):
        self.current_map.objects.remove(self)
        self.current_map.objects.insert(0, self)

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

direction_dict = {'n' : (0, -1), 's': (0, 1), 'e' : (1, 0), 'w' : (-1, 0),
                  'ne' : (1, -1), 'nw' : (-1, -1), 'se' : (1, 1),
                  'sw' : (-1, 1)}

def invert_direction(dx, dy):
    return dx * -1, dy * -1


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

    def swing(self, weapon, d_key):
        weapon.attack(self.owner, d_key)
        attack_tiles = weapon.attack_tiles
        for obj in self.owner.current_map.objects:
            if obj.fighter and (obj.x, obj.y) in attack_tiles:
                self.attack(obj)
            else:
                pass

        self.power_meter = 0

    def shoot(self, weapon, d_key):
        weapon.ranged_attack(self.owner, d_key)
        attack_tiles = weapon.attack_tiles
        for obj in self.owner.current_map.objects:
            if obj.fighter and (obj.x, obj.y) in attack_tiles:
                self.attack(obj)
            else:
                pass

        self.power_meter = 0

    def attack(self, target):
        damage = math.floor((self.power * (self.power_meter / 100) -
                  target.fighter.defense))

        if target is not None:
            if damage > 0:
                log.message(self.owner.name.capitalize() + ' attacks ' +
                            target.name + ' for ' + str(damage) +
                            ' hit points!', colors.orange)
                target.fighter.take_damage(damage)
            else:
                log.message(self.owner.name.capitalize() + ' attacks ' +
                            target.name + ' but it has no effect!', colors.red)

        # self.power_meter = 0

    def recharge(self):
        if self.power_meter < 100:
            self.power_meter += math.floor(100/self.recharge_timer)

    def heal(self, amount):
        self.hp += amount
        if self.hp > self.max_hp:
            self.hp = self.max_hp


distance_to_alpha = {11: 175, 10 : 125, 9 : 100, 8 : 75, 7 : 50, 6 : 25,
                     5: 0, 4 : 0, 3 : 0, 2 : 0, 1 : 0, 0 : 0}

class LightSource:
    def __init__(self, radius, color):
        self.radius = radius
        self.color = color
        self.tiles_lit = []

    def cast_light(self):
        obj = self.owner
        w = obj.current_map.width
        h = obj.current_map.height

        for i in range(0, raycast.RAYS + 1, raycast.STEP):
            ax = raycast.sintable[i]
            ay = raycast.costable[i]

            x, y = obj.x, obj.y

            for z in range(self.radius):
                x += ax
                y += ay

                if x < 0 or y < 0 or x > w or y > h:
                    break

                self.tiles_lit.append((int(round(x)), int(round(y))))

                if obj.current_map.tiles[int(round(x))][int(round(y))] == 0:
                    break

        self.tiles_lit.append((obj.x, obj.y))


class InventorySlot:
    def __init__(self):
        self.stored = None
        self.num_stored = 0


class Inventory:
    def __init__(self):
        self.slot_1 = InventorySlot()
        self.slot_2 = InventorySlot()
        self.slot_3 = InventorySlot()
        self.slot_4 = InventorySlot()
        self.slot_5 = InventorySlot()
        self.slot_weapon = InventorySlot()

        self.slots = {'a' : self.slot_1, 'b' : self.slot_2, 'c' : self.slot_3,
                      'd' : self.slot_4, 'e' : self.slot_5,
                      'w' : self.slot_weapon}

    def pick_up(self, obj):
        if obj.weapon:
            self.drop_weapon()
            self.slot_weapon.stored = obj
            obj.current_map.objects.remove(obj)
        else:
            for key, slot in self.slots.items():
                if slot.stored is None:
                    log.message("You picked up a " + obj.name + "!",
                                colors.white)
                    self.slots[key].stored = obj
                    self.slots[key].num_stored += 1
                    obj.current_map.objects.remove(obj)
                    break


    def list_items(self):
        for key, slot in self.slots.items():
            if slot.stored is None:
                print('Empty')
            else:
                print(slot.name) + ' (' + str(slot.num_stored) + ')'

    def drop_weapon(self):
        weapon = self.slot_weapon.stored
        if weapon is not None:
            weapon.x = self.owner.x
            weapon.y = self.owner.y
            weapon.current_map.objects.append(weapon)
            weapon.send_to_back()
            self.slot_weapon.stored = None

    def get_item_name(self, key):
        if self.slots[key].stored is None:
            return 'Empty'
        else:
            return (self.slots[key].stored.name + ' (' +
                str(self.slots[key].num_stored) + ')')

    def get_item_icon(self, key):
        if self.slots[key].stored is None:
            return 0x0020
        else:
            return self.slots[key].stored.icon

    def remove(self, key):
        self.slots[key].num_stored -= 1
        if self.slots[key].num_stored == 0:
            self.slots[key].stored = None

    @property
    def weapon(self):
        if self.slot_weapon.stored is not None:
            return self.slot_weapon.stored.weapon


class Item:
    def __init__(self, use_function=None):
        self.use_function = use_function

    def use(self, actor, key):
        if self.use_function is None:
            log.message("The " + self.owner.name + " can't be used.",
                        colors.white)
        else:
            if self.use_function(actor) != 'cancelled':
                actor.inventory.remove(key)


class Weapon:
    def __init__(self, power, attack_function=None, ranged=False, radius=0,
                 ammo_icons={}):
        self.power = power
        self.attack_function = attack_function
        self.ranged = ranged
        self.radius = radius
        self.ammo_icons = ammo_icons

        self.attack_tiles = []

    def attack(self, actor, direction_key):
        if self.attack_function is None:
            log.message("This " + self.owner.name + " is useless!",
                        colors.white)
        else:
            if len(self.attack_tiles) > 0:
                del self.attack_tiles[:]

            self.attack_tiles = self.attack_function(actor.x, actor.y,
                                                     direction_key)

    def ranged_attack(self, actor, direction_key):
        source_x = actor.x
        source_y = actor.y
        if self.ranged:
            self.used = True
            i = 0
            while i < self.radius:
                if len(self.attack_tiles) > 0:
                    del self.attack_tiles[:]
                self.attack_tiles = self.attack_function(source_x, source_y,
                                                         direction_key)
                print(self.attack_tiles)
                dx, dy = direction_dict[direction_key]
                if actor.current_map.is_blocked_at(source_x + dx,
                                                   source_y + dy):
                    break
                else:
                    source_x += dx
                    source_y += dy
                    i += 1
                    print(i)
