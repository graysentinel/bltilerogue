from bearlibterminal import terminal
import tdl
import objects
import maps
import gui
import colors
import log
import effects
import raycast
import math

attack_animations = {'west' : 0xE250, 'northwest' : 0xE251,
                     'north' : 0xE252, 'northeast' : 0xE253, 'east': 0xE254,
                     'southeast' : 0xE255, 'south' : 0xE256,
                     'southwest' : 0xE257}


class GameMaster:
    def __init__(self, game_state):
        self.game_state = game_state
        self.players = []
        self.action_queue = []
        self.fps = 30


def player_input(p, gm):
        key = None
        while terminal.has_input():
            key = terminal.read()

        if key in (terminal.TK_CLOSE, terminal.TK_ESCAPE):
            return 'exit'

        camera_window = objects.Window(1, 1, p.camera.width, p.camera.height)
        belt_1 = objects.Window(153, 26, 1, 1)
        belt_2 = objects.Window(153, 29, 1, 1)
        belt_3 = objects.Window(153, 32, 1, 1)
        belt_4 = objects.Window(153, 35, 1, 1)
        belt_5 = objects.Window(153, 38, 1, 1)

        belt_slots = {'a' : belt_1, 'b' : belt_2, 'c' : belt_3, 'd' : belt_4,
                      'e' : belt_5}

        if gm.game_state == 'playing':
            if key == terminal.TK_A:
                player_move_or_attack(p, objects.west)
            elif key == terminal.TK_D:
                player_move_or_attack(p, objects.east)
            elif key == terminal.TK_W:
                player_move_or_attack(p, objects.north)
            elif key == terminal.TK_S:
                player_move_or_attack(p, objects.south)
            elif key == terminal.TK_KP_0 or key == terminal.TK_MOUSE_RIGHT:
                for obj in p.current_map.objects:
                    if obj.x == p.x and obj.y == p.y and obj.item:
                        p.inventory.pick_up(obj)
            elif key == terminal.TK_I:
                p.inventory.list_items()
            elif key == terminal.TK_KP_4:
                player_attack(p, objects.west, 'w')
            elif key == terminal.TK_KP_7:
                player_attack(p, objects.northwest, 'nw')
            elif key == terminal.TK_KP_8:
                player_attack(p, objects.north, 'n')
            elif key == terminal.TK_KP_9:
                player_attack(p, objects.northeast, 'ne')
            elif key == terminal.TK_KP_6:
                player_attack(p, objects.east, 'e')
            elif key == terminal.TK_KP_3:
                player_attack(p, objects.southeast, 'se')
            elif key == terminal.TK_KP_2:
                player_attack(p, objects.south, 's')
            elif key == terminal.TK_KP_1:
                player_attack(p, objects.southwest, 'sw')
            elif key == terminal.TK_KP_5 or key == terminal.TK_MOUSE_MIDDLE:
                p.inventory.switch_active()
            elif key == terminal.TK_1:
                p.inventory.use_item(p, 'a')
            elif key == terminal.TK_2:
                p.inventory.use_item(p, 'b')
            elif key == terminal.TK_3:
                p.inventory.use_item(p, 'c')
            elif key == terminal.TK_4:
                p.inventory.use_item(p, 'd')
            elif key == terminal.TK_5:
                p.inventory.use_item(p, 'e')
            elif key == terminal.TK_MOUSE_LEFT:
                mx = terminal.state(terminal.TK_MOUSE_X)
                my = terminal.state(terminal.TK_MOUSE_Y)
                if camera_window.contains(mx, my):
                    tmx = int(round(mx / 4))
                    tmy = int(round(my / 2))
                    omx, omy = p.camera.offset(tmx, tmy)
                    p.mouse_x = omx
                    p.mouse_y = omy
                    d_key = p.get_direction(omx, omy)
                    d = objects.direction_dict[d_key]
                    if d != 'none':
                        player_attack(p, d, d_key)
                else:
                    for key, window in belt_slots.items():
                        if window.contains(mx, my):
                            p.inventory.use_item(p, key)
            else:
                return 'no-turn'


def player_move_or_attack(p, direction):

    '''
    target = None
    for obj in p.current_map.objects:
        if obj.fighter and (obj.x == x and obj.y == y):
            target = obj
            break

    if target is not None:
        p.fighter.attack(target)

    else:
    '''
    x, y = p.move(direction)
    if not p.current_map.is_blocked_at(x, y):
        p.x, p.y = x, y
        # print("Player Position: ({}, {})".format(p.x, p.y))
        p.camera.move(direction)
        # p.current_map.fov_recompute = True


def player_attack(p, direction, direction_string):
    p.attack = direction_string
    p.attack_direction = direction

    if p.inventory.slot_weapon.active:
        if p.inventory.weapon.ranged:
            p.fighter.shoot(p.inventory.weapon, direction_string)
        else:
            p.fighter.swing(p.inventory.weapon, direction_string)
    else:
        p.fighter.power_meter = 0
        if p.inventory.spell is not None:
            p.inventory.spell.cast(p, direction_string)
            p.inventory.remove('s')
        else:
            log.message('No spell equipped!', colors.light_violet)


def player_death(p):
    log.message('You died!', colors.red)
    p.alive = False
    p.icon = 0xE150


def render(p, gm):
    terminal.clear()

    if p.camera.flash:
        if p.camera.flash_counter < p.camera.flash_frames:
            terminal.layer(3)
            for y in range(p.camera.height):
                for x in range(p.camera.width):
                    gui.terminal_set_color(p.camera.flash_alpha, colors.white)
                    terminal.put(x*4, y*2, 0xE500)
            p.camera.flash_counter += 1
            p.camera.flash_fade()
        else:
            p.camera.flash_deactivate()

    #calculate field of view for all rendering below
    #if map.fov_recompute:
        #map.fov_recompute = False

    ''' Set visible and maximum view distance '''
    visible_tiles = tdl.map.quickFOV(p.x, p.y, p.current_map.is_visible_tile,
                                     fov=p.fov_algo,
                                     radius=p.sight_radius,
                                     lightWalls=p.fov_light_walls)

    player.visible = visible_tiles

    max_visible = tdl.map.quickFOV(p.x, p.y, p.current_map.is_visible_tile,
                                   fov=p.fov_algo, radius=10,
                                   lightWalls=p.fov_light_walls)

    light_source_tiles = []
    lit_tiles = []

    ''' Render Object Layer '''
    terminal.layer(2)
    for o in p.current_map.objects:
        if o.light_source:
            for x, y in o.light_source.tiles_lit:
                # visible_tiles.add((x, y))
                lit_tiles.append((x, y))
                light_source_tiles.append((x, y, o.light_source.color))
            if (o.x, o.y) in max_visible:
                gui.terminal_set_color(255, o.light_source.color)
                o.draw(p.camera)

        else:
            if (o.x, o.y) in max_visible and (o.x, o.y) in lit_tiles:
                o.draw(p.camera)

            if (o.x, o.y) in visible_tiles:
                o.draw(p.camera)

    if not p.inventory.weapon.ranged:
        if p.attack is not None and p.fighter.power_meter < 20:
            if p.inventory.weapon.active:
                for tgt_x, tgt_y in p.inventory.weapon.attack_tiles:
                    weapon_x, weapon_y = p.camera.to_camera_coordinates(tgt_x,
                                                                        tgt_y)
                    terminal.put(weapon_x*4, weapon_y*2, 0xE275)
    else:
        if p.attack is not None:
            pass

    for effect in p.current_map.effects:
        if effect.active:
            for ex, ey, hit in effect.aoe:
                ex2, ey2 = p.camera.to_camera_coordinates(ex, ey)
                if hit:
                    terminal.put(ex2*4, ey2*2, effect.icons['hit'])
                else:
                    terminal.put(ex2*4, ey2*2, effect.icons[p.attack])

    if p.fighter.power_meter >= 20:
        p.attack = None
        p.attack_direction = None
        p.inventory.weapon.active = False

    ''' Render Map Layer '''
    terminal.layer(1)
    camera_x = 1
    camera_y = 1

    gui.separator_box(0, 0, p.camera.width*4, p.camera.height*2, colors.white)

    ''' Render Primary Vision '''
    gui.terminal_set_color(255, colors.light_blue)
    for y in range(camera_x, p.camera.height):
        for x in range(camera_y, p.camera.width):
            tx, ty = p.camera.offset(x, y)
            visible = (tx, ty) in visible_tiles
            if not p.current_map.out_of_bounds(tx, ty):
                tile = p.current_map.tiles[tx][ty]
                if not visible:
                    if p.current_map.tiles_explored[tx][ty] == 1:
                        terminal.put(x*4, y*2,
                                   maps.terrain_types[tile].icon_unseen)
                    else:
                        terminal.put(x*4, y*2, 0xE050)
                else:
                    terminal.put(x*4, y*2, maps.terrain_types[tile].icon_seen)
                    p.current_map.tiles_explored[tx][ty] = 1
            else:
                terminal.put(x*4, y*2, 0xE050)

    ''' Render Light Effects '''
    for y in range(p.camera.height):
        for x in range(p.camera.width):
            vx, vy = p.camera.offset(x, y)
            in_max_visible_range = (vx, vy) in max_visible
            #print(light_source_tiles)
            if in_max_visible_range:
                for lx, ly, lcolor in light_source_tiles:
                    tile = p.current_map.tiles[vx][vy]
                    if lx == vx and ly == vy:
                        d = int(round(p.distance_to_square(lx, ly)))
                        a = objects.distance_to_alpha[d]
                        terminal.layer(4)
                        gui.tile_dimmer(x, y, a)
                        terminal.layer(1)
                        gui.terminal_set_color(255, lcolor)
                        terminal.put(x*4, y*2,
                                     maps.terrain_types[tile].icon_seen)

    ''' Render GUI '''
    terminal.layer(0)
    terminal.color("white")

    right_panel_x = p.camera.width * 4
    right_panel_y = 1
    right_panel_width = terminal.state(terminal.TK_WIDTH) - p.camera.width*4
    right_panel_height = terminal.state(terminal.TK_HEIGHT) - p.camera.height*2

    bottom_panel_x = 1
    bottom_panel_y = (p.camera.height * 2) + 1
    bottom_panel_width = terminal.state(terminal.TK_WIDTH) - right_panel_width
    bottom_panel_height = terminal.state(terminal.TK_HEIGHT) - bottom_panel_y

    h = terminal.state(terminal.TK_HEIGHT)
    w = terminal.state(terminal.TK_WIDTH)

    # Player Name
    gui.separator_box(right_panel_x, 0, right_panel_width, 2, colors.white)

    terminal.puts(right_panel_x + 2, right_panel_y, p.name.capitalize(),
                  right_panel_width-4, 1, terminal.TK_ALIGN_TOP |
                  terminal.TK_ALIGN_CENTER)

    # HP Bar
    gui.separator_box(right_panel_x, right_panel_y+1, right_panel_width, 2,
                      colors.white)
    gui.render_bar(right_panel_x + 2, right_panel_y + 2, right_panel_width-4,
                   'HP', p.fighter.hp, p.fighter.max_hp, colors.red,
                   colors.darker_red, "Health: " + str(p.fighter.hp) + "/" +
                   str(p.fighter.max_hp))

    # Stamina Bar
    gui.separator_box(right_panel_x, right_panel_y + 3, right_panel_width, 2,
                      colors.white)
    gui.render_bar(right_panel_x + 2, right_panel_y + 4, right_panel_width-4,
                   'attack power', p.fighter.power_meter, 100,
                   colors.orange, colors.darker_orange, "Stamina")

    # Mana Bar
    gui.separator_box(right_panel_x, right_panel_y + 5, right_panel_width, 2,
                      colors.white)
    gui.render_bar(right_panel_x + 2, right_panel_y + 6, right_panel_width-4,
                   'mana', 30, 30, colors.dark_blue, colors.darker_blue, "Mana")


    # Weapon, Spell & Armor #
    '''
    terminal.puts(right_panel_x, right_panel_y+8, "Inventory",
                  right_panel_width, 1, terminal.TK_ALIGN_TOP |
                  terminal.TK_ALIGN_CENTER)
    '''
    gui.separator_box(right_panel_x, right_panel_y+7, right_panel_width, 15,
                      colors.white, title="Inventory")

    inventory_x = right_panel_x + 2
    inventory_y = right_panel_y + 10

    # Current Weapon
    if p.inventory.slots['w'].active:
        gui.highlight_box(inventory_x, inventory_y, p.inventory, 'w',
                          colors.yellow)
    else:
        gui.highlight_box(inventory_x, inventory_y, p.inventory, 'w',
                          colors.black)
    terminal.puts(inventory_x + 6, inventory_y + 1, "Strength: " +
                  str(p.fighter.power))

    # Equipped Spell
    if p.inventory.slots['s'].active:
        gui.highlight_box(inventory_x, inventory_y + 3, p.inventory, 's',
                          colors.yellow)
    else:
        gui.highlight_box(inventory_x, inventory_y + 3, p.inventory, 's',
                          colors.black)

    gui.terminal_reset_color()

    terminal.puts(inventory_x + 6, inventory_y + 4,
                  p.inventory.get_item_name('s'))

    # Defense Icon
    terminal.put(inventory_x + 2, inventory_y + 7, 0xE300)
    terminal.puts(inventory_x + 6, inventory_y + 7, "Defense: " +
                  str(p.fighter.defense))

    # Belt Slots #
    gui.separator_box(right_panel_x, right_panel_y+22, right_panel_width,
                      21, colors.white, title="Belt")
    '''
    terminal.puts(right_panel_x, right_panel_y+23, "Belt", right_panel_width,
                  1, terminal.TK_ALIGN_TOP | terminal.TK_ALIGN_CENTER)
    '''

    terminal.puts(right_panel_x + 2, right_panel_y + 26, "1")
    gui.render_box(right_panel_x + 4, right_panel_y + 25,
                   p.inventory, 'a')

    terminal.puts(right_panel_x + 2, right_panel_y + 29, "2")
    gui.render_box(right_panel_x + 4, right_panel_y + 28,
                   p.inventory, 'b')

    terminal.puts(right_panel_x + 2, right_panel_y + 32, "3")
    gui.render_box(right_panel_x + 4, right_panel_y + 31,
                   p.inventory, 'c')

    terminal.puts(right_panel_x + 2, right_panel_y + 35, "4")
    gui.render_box(right_panel_x + 4, right_panel_y + 34,
                   p.inventory, 'd')

    terminal.puts(right_panel_x + 2, right_panel_y + 38, "5")
    gui.render_box(right_panel_x + 4, right_panel_y + 37,
                   p.inventory, 'e')

    '''terminal.puts(right_panel_x + 8, right_panel_y + 26,
                  p.inventory.get_item_name('a'))'''

    '''terminal.puts(right_panel_x, right_panel_y+1, "Power: " +
                  str(p.fighter.power_meter) + "/100", right_panel_width,
                  right_panel_height, terminal.TK_ALIGN_TOP |
                  terminal.TK_ALIGN_CENTER)'''

    gui.separator_box(0, bottom_panel_y-1, w-right_panel_width, 7, colors.white)
    msg_line = 1
    for line, msg_color in log.game_messages:
        gui.terminal_set_color(255, msg_color)
        terminal.puts(bottom_panel_x+1, bottom_panel_y+msg_line-1, line)
        msg_line += 1

    gui.terminal_set_color(255, colors.white)

    gui.separator_box(right_panel_x, bottom_panel_y-1, right_panel_width,
                      7, colors.white)

    terminal.puts(right_panel_x, bottom_panel_y+2, "Player Position: " +
                  p.current_position, right_panel_width, 1,
                  terminal.TK_ALIGN_MIDDLE | terminal.TK_ALIGN_CENTER)
    '''
    mx = int(round(terminal.state(terminal.TK_MOUSE_X) / 4))
    my = int(round(terminal.state(terminal.TK_MOUSE_Y) / 2))

    cmx, cmy = p.camera.offset(mx, my)
    '''
    terminal.puts(right_panel_x, bottom_panel_y+3, "Cursor Position: (" +
                  str(p.mouse_x) + "," + str(p.mouse_y) + ')',
                  right_panel_width,
                  1, terminal.TK_ALIGN_TOP | terminal.TK_ALIGN_CENTER)

    terminal.refresh()


def current_layer():
    return terminal.state(terminal.TK_LAYER)

# Initialize Window
terminal.open()
terminal.set("""U+E000: assets/rogue.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E050: assets/floors.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E060: assets/walls.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E070: assets/doors.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E100: assets/basic-monsters.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E150: assets/corpse.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E200: assets/items.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E250: assets/weapons.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E275: assets/swordslash.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E300: assets/armor.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E350: assets/arrows.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E360: assets/spellbooks.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E370: assets/lightning_bolt.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E380: assets/fireball.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E500: assets/white.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("window: size=181x52, cellsize=auto, title='roguelike'")
terminal.set("input.filter={keyboard, mouse+}")
terminal.composition(True)

# Initialize Game
player_fighter = objects.Fighter(hp=30, defense=2, power=5, recharge=20,
                                 death_function=player_death)
player = objects.GameObject('player', 1, 1, 0xE000, fighter=player_fighter,
                            update_func=objects.update_player)
dungeon_map = maps.DungeonMap(50, 50)
dungeon_map.make_map(player)
dungeon_map.objects.append(player)

player.current_map = dungeon_map
player.action = None
player.fov_algo = 'BASIC'
player.fov_light_walls = True
player.object_id = 'p1'
player.alive = True
player.sight_radius = 3
player.attack = None
player.attack_direction = None
player.mouse_x = 0
player.mouse_y = 0

inv = objects.Inventory()
player.inventory = inv
player.inventory.owner = player

'''
sword_wpn = objects.Weapon(2, effects.sword_attack)
sword = objects.GameObject('sword', 0, 0, 0xE251, weapon=sword_wpn)
inv.slot_weapon.stored = sword
'''

axe_wpn = objects.Weapon(2, effects.axe_attack)
axe_item = objects.Item()
axe = objects.GameObject('axe', 0, 0, 0xE250, item=axe_item, weapon=axe_wpn,
                         active=False)
axe.current_map = dungeon_map
inv.slot_weapon.stored = axe

player_cam1 = objects.Camera(0, 0, 37, 22)
player.camera = player_cam1
player.camera.center_view(player)

game = GameMaster('playing')

log.message("Welcome to the jungle.", colors.red)

# Main Game Loop
while True:
    # Check game state
    if not player.alive:
        game.game_state = 'dead'

    render(player, game)

    terminal.layer(2)
    for o in dungeon_map.objects:
        o.clear(player.camera)

    '''
    for obj in dungeon_map.objects:
        if obj.ai:
            obj.ai.take_turn()
        if obj.fighter:
            obj.fighter.recharge()
    '''

    for obj in dungeon_map.objects:
        if obj.active:
            obj.update()

    for effect in dungeon_map.effects:
        if effect.active:
            effect.update()

    dungeon_map.update()

    player.action = player_input(player, game)
    if player.action == 'exit':
        break

    terminal.delay(1000 // game.fps)
