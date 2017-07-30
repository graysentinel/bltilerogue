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
        self.fps = 30

    def add_player(self, game, player_name):
        player_id = game.game_id + str(len(game.players))
        player_fighter = objects.Fighter(hp=30, defense=2, power=5, recharge=20,
                                         death_function=Player.death)
        p_inv = objects.Inventory()
        p_avatar = objects.GameObject(name=player_name, x=1, y=1, icon=0xE000,
                                       inventory=p_inv, fighter=player_fighter,
                                       current_map=None, player_flag=True,
                                       update_func=objects.update_player)
        player_cam = objects.Camera(0, 0, 37, 22)
        player = Player(id=player_id, name=player_name, camera=player_cam,
                         avatar=p_avatar, fov_algo='BASIC', light_walls=True,
                         sight_radius=3)
        return player

    def start_new_game(self):
        game_id = 'test'
        new_game = Game('test')

        p1 = self.add_player(new_game, 'player')
        new_game.players.append(p1)
        dungeon_map = maps.DungeonMap(50, 50)
        dungeon_map.make_map(p1.avatar)
        p1.camera.center_view(p1.avatar)
        new_game.map_log.append(dungeon_map)
        new_game.current_map = dungeon_map

        for player in new_game.players:
            dungeon_map.objects.append(player.avatar)
            player.avatar.current_map = dungeon_map

        log.message("The dungeon awaits, pathetic mortal.", colors.red)

        return new_game


class Game:
    def __init__(self, game_id):
        self.game_id = game_id
        self.map_log = []
        self.players = []
        self.message_log = []
        self.current_map = None
        self.state = 'playing'

    def play(self, game_master):
        while not game_master.game_state == 'quit':
            # Check game state
            for player in self.players:
                if not player.avatar.alive:
                    game_master.game_state = 'dead'

            current_player = self.players[0]

            render(current_player, game_master)

            terminal.layer(2)
            for o in self.current_map.objects:
                o.clear(current_player.camera)

            for obj in self.current_map.objects:
                if obj.active:
                    obj.update()

            for effect in self.current_map.effects:
                if effect.active:
                    effect.update()

            self.current_map.update()

            player.action = current_player.input(self)
            if player.action == 'quit':
                game_master.game_state = 'quit'

            terminal.delay(1000 // game_master.fps)


class Player:
    def __init__(self, id, name, camera, avatar, fov_algo, light_walls,
                 sight_radius):
        self.id = id
        self.name = name
        self.camera = camera
        self.avatar = avatar
        self.fov_algo = fov_algo
        self.fov_light_walls = light_walls
        self.sight_radius = sight_radius

        self.mouse_x = 0
        self.mouse_y = 0
        self.action = None
        self.visible = None
        self.avatar.owner = self

    def move(self, direction):
        x, y = self.avatar.move(direction)
        if not self.avatar.current_map.is_blocked_at(x, y):
            self.avatar.x, self.avatar.y = x, y
            self.camera.move(direction)

    def attack(self, direction_key):
        p = self.avatar
        p.attack = direction_key
        p.attack_direction = objects.direction_dict[direction_key]

        if p.inventory.slot_weapon.active:
            if p.inventory.weapon is not None:
                if p.inventory.weapon.ranged:
                    p.fighter.shoot(p.inventory.weapon, direction_key)
                else:
                    p.fighter.swing(p.inventory.weapon, direction_key)
            else:
                log.message('No weapon equipped!', colors.yellow)
        else:
            p.fighter.power_meter = 0
            if p.inventory.spell is not None:
                p.inventory.spell.cast(p, direction_key)
                p.inventory.remove('s')
            else:
                log.message('No spell equipped!', colors.light_violet)

    def input(self, game):
        p = self.avatar
        key = None

        while terminal.has_input():
            key = terminal.read()

        if key in (terminal.TK_CLOSE, terminal.TK_ESCAPE):
            return 'quit'

        camera_window = objects.Window(1, 1, self.camera.width,
                                       self.camera.height)
        belt_1 = objects.Window(153, 26, 1, 1)
        belt_2 = objects.Window(153, 29, 1, 1)
        belt_3 = objects.Window(153, 32, 1, 1)
        belt_4 = objects.Window(153, 35, 1, 1)
        belt_5 = objects.Window(153, 38, 1, 1)

        belt_slots = {'a' : belt_1, 'b' : belt_2, 'c' : belt_3, 'd' : belt_4,
                      'e' : belt_5}

        if game.state == 'playing':
            if key == terminal.TK_A:
                self.move(objects.west)
            elif key == terminal.TK_D:
                self.move(objects.east)
            elif key == terminal.TK_W:
                self.move(objects.north)
            elif key == terminal.TK_S:
                self.move(objects.south)
            elif key == terminal.TK_KP_0 or key == terminal.TK_MOUSE_RIGHT:
                for obj in p.current_map.objects:
                    if obj.x == p.x and obj.y == p.y and obj.item:
                        p.inventory.pick_up(obj)
            elif key == terminal.TK_I:
                p.inventory.list_items()
            elif key == terminal.TK_KP_4:
                self.attack('w')
            elif key == terminal.TK_KP_7:
                self.attack('nw')
            elif key == terminal.TK_KP_8:
                self.attack('n')
            elif key == terminal.TK_KP_9:
                self.attack('ne')
            elif key == terminal.TK_KP_6:
                self.attack('e')
            elif key == terminal.TK_KP_3:
                self.attack('se')
            elif key == terminal.TK_KP_2:
                self.attack('s')
            elif key == terminal.TK_KP_1:
                self.attack('sw')
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
                    omx, omy = self.camera.offset(tmx, tmy)
                    self.mouse_x = omx
                    self.mouse_y = omy
                    d_key = p.get_direction(omx, omy)
                    if d_key != 'none':
                        d = objects.direction_dict[d_key]
                        self.attack(d_key)
                else:
                    for key, window in belt_slots.items():
                        if window.contains(mx, my):
                            p.inventory.use_item(p, key)
            else:
                return 'no-turn'

    @staticmethod
    def death(avatar):
        log.message('You died!', colors.red)
        avatar.alive = False
        avatar.icon = 0xE150


def render(player, gm):
    terminal.clear()
    p = player.avatar

    if player.camera.flash:
        if player.camera.flash_counter < player.camera.flash_frames:
            terminal.layer(3)
            for y in range(player.camera.height):
                for x in range(player.camera.width):
                    gui.terminal_set_color(player.camera.flash_alpha,
                                           colors.white)
                    terminal.put(x*4, y*2, 0xE500)
            player.camera.flash_counter += 1
            player.camera.flash_fade()
        else:
            player.camera.flash_deactivate()

    #calculate field of view for all rendering below
    #if map.fov_recompute:
        #map.fov_recompute = False

    ''' Set visible and maximum view distance '''
    visible_tiles = tdl.map.quickFOV(p.x, p.y, p.current_map.is_visible_tile,
                                     fov=player.fov_algo,
                                     radius=player.sight_radius,
                                     lightWalls=player.fov_light_walls)

    player.visible = visible_tiles

    max_visible = tdl.map.quickFOV(p.x, p.y, p.current_map.is_visible_tile,
                                   fov=player.fov_algo, radius=10,
                                   lightWalls=player.fov_light_walls)

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
                o.draw(player.camera)

        else:
            if (o.x, o.y) in max_visible and (o.x, o.y) in lit_tiles:
                o.draw(player.camera)

            if (o.x, o.y) in visible_tiles:
                o.draw(player.camera)

    if p.inventory.weapon is not None:
        if not p.inventory.weapon.ranged:
            if p.attack is not None and p.fighter.power_meter < 20:
                if p.inventory.weapon.active:
                    for tgt_x, tgt_y in p.inventory.weapon.attack_tiles:
                        weapon_x, weapon_y = player.camera.to_camera_coordinates(tgt_x, tgt_y)
                        terminal.put(weapon_x*4, weapon_y*2, 0xE275)
        else:
            if p.attack is not None:
                pass

    for effect in p.current_map.effects:
        if effect.active:
            for ex, ey, hit in effect.aoe:
                ex2, ey2 = player.camera.to_camera_coordinates(ex, ey)
                if hit:
                    terminal.put(ex2*4, ey2*2, effect.icons['hit'])
                else:
                    terminal.put(ex2*4, ey2*2, effect.icons[p.attack])

    if p.inventory.weapon is not None:
        if p.fighter.power_meter >= 20:
            p.attack = None
            p.attack_direction = None
            p.inventory.weapon.active = False

    ''' Render Map Layer '''
    terminal.layer(1)
    camera_x = 1
    camera_y = 1

    gui.separator_box(0, 0, player.camera.width*4, player.camera.height*2,
                      colors.white)

    ''' Render Primary Vision '''
    gui.terminal_set_color(255, colors.light_blue)
    for y in range(camera_x, player.camera.height):
        for x in range(camera_y, player.camera.width):
            tx, ty = player.camera.offset(x, y)
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
    for y in range(player.camera.height):
        for x in range(player.camera.width):
            vx, vy = player.camera.offset(x, y)
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

    right_panel_x = player.camera.width * 4
    right_panel_y = 1
    right_panel_width = (terminal.state(terminal.TK_WIDTH) -
                         player.camera.width*4)
    right_panel_height = (terminal.state(terminal.TK_HEIGHT) -
                         player.camera.height*2)

    bottom_panel_x = 1
    bottom_panel_y = (player.camera.height * 2) + 1
    bottom_panel_width = terminal.state(terminal.TK_WIDTH) - right_panel_width
    bottom_panel_height = terminal.state(terminal.TK_HEIGHT) - bottom_panel_y

    h = terminal.state(terminal.TK_HEIGHT)
    w = terminal.state(terminal.TK_WIDTH)

    # Player Name
    gui.separator_box(right_panel_x, 0, right_panel_width, 2, colors.white)

    terminal.puts(right_panel_x + 2, right_panel_y, player.name.capitalize(),
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

    cmx, cmy = player.camera.offset(mx, my)
    '''
    terminal.puts(right_panel_x, bottom_panel_y+3, "Cursor Position: (" +
                  str(player.mouse_x) + "," + str(player.mouse_y) + ')',
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
the_gm = GameMaster('playing')
new_game = the_gm.start_new_game()
new_game.play(game_master=the_gm)
