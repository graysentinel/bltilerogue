from bearlibterminal import terminal
import math
import log
import colors
import raycast


''' Update Functions '''

def update_default(obj):
    pass

def update_monster(monster):
    monster.ai.update()
    monster.fighter.update()

def update_player(player):
    player.fighter.update()
    # player.inventory.weapon.update()

def update_ammo(ammo):
    ammo.projectile.update()
    if ammo.spell:
        ammo.spell.update()

def update_spell(spellbook):
    spellbook.spell.update()

def update_spell_projectile(spell):
    spell.projectile.update()
    spell.spell.update()

''' Classes and Data Structures '''

class Window:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.x2 = self.x + self.w*4
        self.y2 = self.y + self.h*2

    def contains(self, x, y):
        if x > self.x and y > self.y and x < self.x2 and y < self.y2:
            return True
        else:
            return False


class GameObject:
    def __init__(self, name, x, y, icon, blocks=False, fighter=None, ai=None,
                 light_source=None, item=None, weapon=None, projectile=None,
                 spell=None, update_func=update_default, active=True):
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

        self.projectile = projectile
        if self.projectile:
            self.projectile.owner = self

        self.spell = spell
        if self.spell:
            self.spell.owner = self

        self.update_func = update_func
        self.active = active

        self.object_id = None

    def draw(self, camera):
        x, y = camera.to_camera_coordinates(self.x, self.y)
        if self.projectile:
            terminal.put_ext(x*4, y*2, self.projectile.x_offset,
                             self.projectile.y_offset, self.icon)
        else:
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

    def update(self):
        self.update_func(self)

    def get_direction(self, x, y):
        if x > self.x and y > self.y:
            return 'se'
        elif x > self.x and y == self.y:
            return 'e'
        elif x < self.x and y == self.y:
            return 'w'
        elif x < self.x and y < self.y:
            return 'nw'
        elif x == self.x and y < self.y:
            return 'n'
        elif x == self.x and y > self.y:
            return 's'
        elif x < self.x and y > self.y:
            return 'sw'
        elif x > self.x and y < self.y:
            return 'ne'
        elif x == self.x and y == self.y:
            return 'none'

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

        self.flash = False
        self.flash_frames = 30
        self.flash_alpha = 255
        self.flash_fade_counter = 5
        self.flash_counter = 0

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

        if x in range(self.x, self.x2) and y in range(self.y, self.y2):
            return True

        return False

    def offset(self, x, y):
        return x + self.x, y + self.y

    def to_camera_coordinates(self, x, y):
        (x, y) = (x - self.x, y - self.y)
        return x, y

    def flash_activate(self):
        self.flash = True

    def flash_deactivate(self):
        self.flash = False
        self.flash_counter = 0
        self.flash_alpha = 255

    def flash_fade(self):
        if self.flash_counter % self.flash_fade_counter == 0:
            self.flash_alpha -= 50

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

keypad_to_directions = {terminal.TK_KP_1 : 'sw', terminal.TK_KP_2 : 's',
                        terminal.TK_KP_3 : 'se', terminal.TK_KP_4 : 'w',
                        terminal.TK_KP_6 : 'e', terminal.TK_KP_7 : 'nw',
                        terminal.TK_KP_8 : 'n', terminal.TK_KP_9 : 'ne'}

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
        self.shooting = False
        self.weapon = None
        self.d_key = ''
        self.frames = 0
        self.attack_delay = 5

    def take_damage(self, damage):
        if damage > 0:
            self.hp -= damage

        if self.hp <= 0:
            function = self.death_function
            if function is not None:
                function(self.owner)

    def swing(self, weapon, d_key):
        weapon.active = True
        weapon.attack(self.owner.x, self.owner.y, d_key)
        attack_tiles = weapon.attack_tiles
        for obj in self.owner.current_map.objects:
            if obj.fighter and (obj.x, obj.y) in attack_tiles:
                self.attack(obj)
            else:
                pass

        self.power_meter = 0

    def shoot(self, weapon, d_key):
        damage = math.floor(self.power * (self.power_meter / 100))
        weapon.ranged_attack(self.owner, d_key, damage)
        self.power_meter = 0
        '''
        attack_tiles = weapon.attack_tiles
        if len(attack_tiles) == 0:
            self.deactivate_bow()
        else:
            for obj in self.owner.current_map.objects:
                if obj.fighter and (obj.x, obj.y) in attack_tiles:
                    self.attack(obj)
                else:
                    pass
        '''

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

    def update(self):
        self.recharge()

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
    def __init__(self, active=False):
        self.active = active
        self.stored = None
        self.num_stored = 0


class Inventory:
    def __init__(self):
        self.slot_1 = InventorySlot()
        self.slot_2 = InventorySlot()
        self.slot_3 = InventorySlot()
        self.slot_4 = InventorySlot()
        self.slot_5 = InventorySlot()
        self.slot_weapon = InventorySlot(active=True)
        self.slot_spell = InventorySlot()

        self.slots = {'a' : self.slot_1, 'b' : self.slot_2, 'c' : self.slot_3,
                      'd' : self.slot_4, 'e' : self.slot_5,
                      's' : self.slot_spell, 'w' : self.slot_weapon}

    def pick_up(self, obj):
        if obj.weapon:
            self.drop('w')
            self.slot_weapon.stored = obj
            obj.current_map.objects.remove(obj)
        elif obj.spell:
            self.drop('s')
            self.slot_spell.stored = obj
            self.slot_spell.num_stored = obj.spell.charges
            obj.current_map.objects.remove(obj)
        else:
            for key, slot in self.slots.items():
                if slot.stored is None:
                    self.slots[key].stored = obj
                    self.slots[key].num_stored += 1
                    obj.current_map.objects.remove(obj)
                    break

        log.message("You picked up a " + obj.name + "!", colors.white)

    def use_item(self, actor, key):
        if self.slots[key].stored is not None:
            if self.slots[key].stored.item.use(actor) != 'cancelled':
                self.remove(key)
        else:
            log.message('That inventory slot is empty!', colors.yellow)

    def list_items(self):
        for key, slot in self.slots.items():
            if slot.stored is None:
                print('Empty')
            else:
                print(slot.name) + ' (' + str(slot.num_stored) + ')'

    def drop(self, key):
        item = self.slots[key].stored
        if item is not None:
            item.x = self.owner.x
            item.y = self.owner.y
            item.current_map.objects.append(item)
            item.send_to_back()
            self.slots[key].stored = None

    def get_item_name(self, key):
        if self.slots[key].stored is None:
            return 'Empty'
        else:
            if key == 's':
                return (self.slots[key].stored.spell.name +
                       ' (' + str(self.slots[key].num_stored) + ')')
            else:
                return (self.slots[key].stored.name + ' (' +
                    str(self.slots[key].num_stored) + ')')

    def get_item_icon(self, key):
        if self.slots[key].stored is None:
            if key != 's':
                return 0x0020
            else:
                return 0xE365
        else:
            return self.slots[key].stored.icon

    def remove(self, key):
        self.slots[key].num_stored -= 1
        if self.slots[key].num_stored == 0:
            self.slots[key].stored = None

    def switch_active(self):
        if self.slot_weapon.active:
            if self.slot_spell.stored is not None:
                self.slot_weapon.active = False
                self.slot_spell.active = True
            else:
                log.message('No spell equipped!', colors.light_violet)
        elif self.slot_spell.active:
            self.slot_spell.active = False
            self.slot_weapon.active = True

    @property
    def weapon(self):
        if self.slot_weapon.stored is not None:
            return self.slot_weapon.stored.weapon

    @property
    def spell(self):
        if self.slot_spell.stored is not None:
            return self.slot_spell.stored.spell


class Item:
    def __init__(self, use_function=None):
        self.use_function = use_function

    def use(self, actor):
        if self.use_function is None:
            log.message("The " + self.owner.name + " can't be used.",
                        colors.white)
        else:
            return self.use_function(actor)


class Weapon:
    def __init__(self, power, attack_function=None, ranged=False, radius=0,
                 ammo_icons={}, ammo_name=''):
        self.power = power
        self.attack_function = attack_function
        self.ranged = ranged
        self.radius = radius
        self.ammo_icons = ammo_icons
        self.ammo_name = ammo_name

        self.active = False
        self.attack_tiles = []

    def attack(self, source_x, source_y, direction_key):
        if self.attack_function is None:
            log.message("This " + self.owner.name + " is useless!",
                        colors.white)
        else:
            self.source_x = source_x
            self.source_y = source_y
            self.direction_key = direction_key
            if len(self.attack_tiles) > 0:
                del self.attack_tiles[:]

            self.attack_tiles = self.attack_function(source_x, source_y,
                                                     self.direction_key)

    def ranged_attack(self, source, direction_key, damage):

        proj = self.attack_function(source, self.radius, direction_key, damage)
        dx, dy = direction_dict[direction_key]
        fired_shot = GameObject(self.ammo_name, source.x+dx, source.y+dy,
                                self.ammo_icons[direction_key],
                                update_func=update_ammo,
                                projectile=proj)
        fired_shot.current_map = source.current_map
        source.current_map.objects.append(fired_shot)


class Projectile:
    def __init__(self, dx, dy, power, weapon_range, aoe):
        self.dx = dx
        self.dy = dy
        self.power = power
        self.range = weapon_range
        self.aoe = aoe
        self.range_counter = 0
        self.collision = False

        self.frames = 0
        self.delay = 3

        self.x_offset = 0
        self.y_offset = 0

    def check_collision(self):
        if not self.aoe:
            if self.owner.current_map.is_blocked_at(self.owner.x + self.dx,
                                                    self.owner.y + self.dy):
                for obj in self.owner.current_map.objects:
                    if obj.fighter and (obj.x == self.owner.x + self.dx and
                                        obj.y == self.owner.y + self.dy):
                        self.hit(obj)
                        self.collision = True
                    else:
                        self.collision = True
        else:
            if self.owner.current_map.is_blocked_at(self.owner.x + self.dx,
                                                    self.owner.y + self.dy):
                self.hit_aoe()
                self.collision = True

    def cleanup(self):
        self.owner.active = False
        self.owner.current_map.objects.remove(self.owner)

    def hit_aoe(self):
        if self.owner.spell:
            self.owner.spell.cast(self.owner, 'n')
        else:
            # implement non-magical aoe projectiles?
            pass

    def hit(self, target):
        if not self.owner.spell:
            damage = self.power - target.fighter.defense
            log.message('The ' + target.name + ' is hit by the ' +
                        self.owner.name + ' for ' + str(self.power) +
                        ' damage!', colors.orange)
            target.fighter.take_damage(damage)
        else:
            self.owner.spell.cast(self.owner, 'n')

    def move(self):
        self.owner.x += self.dx
        self.owner.y += self.dy

    def fly(self):
        cells = terminal.state(terminal.TK_CELL_WIDTH) * 4
        base_offset = int(round(cells / self.delay))

        self.x_offset = (base_offset * self.frames) * self.dx
        self.y_offset = (base_offset * self.frames) * self.dy
        '''
        self.x_offset = ((int(round(terminal.state(terminal.TK_CELL_WIDTH) *
                         self.frames))) * self.dx)
        self.y_offset = ((int(round(terminal.state(terminal.TK_CELL_WIDTH) *
                                       self.frames - 4))) * self.dy)
        '''

    def update(self):
        self.frames += 1
        self.fly()
        if self.frames == self.delay:
            if self.range_counter < self.range:
                self.check_collision()
                if not self.collision:
                    self.move()
                    self.range_counter += 1
                    self.frames = 0
                    self.x_offset = 0
                    self.y_offset = 0
                else:
                    self.cleanup()
            else:
                self.cleanup()


class SpellEffect:
    def __init__(self, name, spell_range, damage, render_frames, icons, charges,
                 aoe_function=None):
        self.name = name
        self.range = spell_range
        self.damage = damage
        self.render_frames = render_frames
        self.icons = icons
        self.charges = charges
        self.aoe_function = aoe_function
        self.aoe = None
        self.active = False
        self.frames = 0


    def cast(self, source, d_key):
        aoe = self.aoe_function(source, self.range, d_key)
        if type(aoe) is list:
            self.aoe = aoe
            source.current_map.effects.append(self)
            self.active = True
            for obj in source.current_map.objects:
                if obj.fighter and (obj.x, obj.y, True) in self.aoe:
                    log.message("The " + obj.name + " takes " +
                                str(self.damage) + " damage from the " +
                                self.name + "!", colors.violet)
                    obj.fighter.take_damage(self.damage)
                    if obj.name == 'player' and obj.camera:
                        obj.camera.flash_activate()
        elif type(aoe) is GameObject:
            aoe.current_map = source.current_map
            source.current_map.objects.append(aoe)

    def update(self):
        self.frames += 1
        if self.frames == self.render_frames:
            self.active = False
            self.frames = 0
