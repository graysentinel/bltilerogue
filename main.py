from bearlibterminal import terminal
import tdl
import objects
import maps
import gui
import colors
import log

attack_animations = {'west' : 0xE250, 'northwest' : 0xE251,
                     'north' : 0xE252, 'northeast' : 0xE253, 'east': 0xE254,
                     'southeast' : 0xE255, 'south' : 0xE256,
                     'southwest' : 0xE257}


class GameMaster:
    def __init__(self, game_state):
        self.game_state = game_state
        self.players = []
        self.action_queue = []
        self.fps = 25


def player_input(p, gm):
        key = None
        while terminal.has_input():
            key = terminal.read()

        if key in (terminal.TK_CLOSE, terminal.TK_ESCAPE):
            return 'exit'

        if gm.game_state == 'playing':
            if key == terminal.TK_A:
                player_move_or_attack(p, objects.west)
            elif key == terminal.TK_D:
                player_move_or_attack(p, objects.east)
            elif key == terminal.TK_W:
                player_move_or_attack(p, objects.north)
            elif key == terminal.TK_S:
                player_move_or_attack(p, objects.south)
            elif key == terminal.TK_COMMA:
                for obj in p.current_map.objects:
                    if obj.x == p.x and obj.y == p.y and obj.item:
                        p.inventory.pick_up(obj)
            elif key == terminal.TK_I:
                p.inventory.list_items()
            elif key == terminal.TK_KP_4:
                player_attack(p, objects.west, 'west')
            elif key == terminal.TK_KP_7:
                player_attack(p, objects.northwest, 'northwest')
            elif key == terminal.TK_KP_8:
                player_attack(p, objects.north, 'north')
            elif key == terminal.TK_KP_9:
                player_attack(p, objects.northeast, 'northeast')
            elif key == terminal.TK_KP_6:
                player_attack(p, objects.east, 'east')
            elif key == terminal.TK_KP_3:
                player_attack(p, objects.southeast, 'southeast')
            elif key == terminal.TK_KP_2:
                player_attack(p, objects.south, 'south')
            elif key == terminal.TK_KP_1:
                player_attack(p, objects.southwest, 'southwest')
            else:
                return 'no-turn'


def player_move_or_attack(p, direction):

    target = None
    x, y = p.move(direction)
    for obj in p.current_map.objects:
        if obj.fighter and (obj.x == x and obj.y == y):
            target = obj
            break
    '''
    if target is not None:
        p.fighter.attack(target)

    else:
    '''
    if not p.current_map.is_blocked_at(x, y):
        p.x, p.y = x, y
        # print("Player Position: ({}, {})".format(p.x, p.y))
        p.camera.move(direction)
        # p.current_map.fov_recompute = True


def player_attack(p, direction, direction_string):
    p.attack = direction_string
    p.attack_direction = direction
    target = None
    target_x = p.x + direction.goal_x
    target_y = p.y + direction.goal_y

    for obj in p.current_map.objects:
        if obj.fighter and (obj.x == target_x and obj.y == target_y):
            target = obj
            break

    if target is not None:
        p.fighter.attack(target)


def player_death(p):
    log.message('You died!', colors.red)
    p.alive = False
    p.icon = 0xE150


def render(p, gm):

    terminal.clear()
    #calculate field of view for all rendering below
    #if map.fov_recompute:
        #map.fov_recompute = False

    ''' Set visible and maximum view distance '''
    visible_tiles = tdl.map.quickFOV(p.x, p.y, p.current_map.is_visible_tile,
                                     fov=p.fov_algo,
                                     radius=p.sight_radius,
                                     lightWalls=p.fov_light_walls)

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

    if p.attack is not None and p.fighter.power_meter < 20:
        target_x = p.x + p.attack_direction.goal_x
        target_y = p.y + p.attack_direction.goal_y
        weapon_x, weapon_y = p.camera.to_camera_coordinates(target_x, target_y)
        # terminal.put(target_x, target_y, attack_animations[p.attack])
        terminal.put(weapon_x*4, weapon_y*2, attack_animations[p.attack])

    if p.fighter.power_meter >= 20:
        p.attack = None
        p.attack_direction = None

    ''' Render Map Layer '''
    terminal.layer(1)

    ''' Render Primary Vision '''
    gui.terminal_set_color(255, colors.light_blue)
    for y in range(p.camera.height):
        for x in range(p.camera.width):
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

    for y in range(0, terminal.TK_HEIGHT-bottom_panel_height):
        terminal.put(right_panel_x, y, 0x2588)

    terminal.puts(right_panel_x + 2, right_panel_y, "Player HP: " +
                  str(p.fighter.hp) + "/" + str(p.fighter.max_hp),
                  right_panel_width, right_panel_height,
                  terminal.TK_ALIGN_TOP | terminal.TK_ALIGN_LEFT)

    terminal.puts(right_panel_x + 2, right_panel_y + 2, "Attack Power")

    gui.render_bar(right_panel_x + 2, right_panel_y + 3, right_panel_width-4,
                   'attack power', p.fighter.power_meter, 100,
                   colors.darker_red)

    inventory_x = right_panel_x + 4
    inventory_y = right_panel_y + 5

    terminal.put(inventory_x, inventory_y, 0xE253)
    terminal.puts(inventory_x + 4, inventory_y, "Strength: " +
                  str(p.fighter.power))

    terminal.put(inventory_x, inventory_y + 2, 0xE300)
    terminal.puts(inventory_x + 4, inventory_y + 2, "Defense: " +
                  str(p.fighter.defense))

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

    for x in range(0, terminal.TK_WIDTH):
        terminal.put(x, bottom_panel_y-1, 0x2588)

    msg_line = 1
    for line, msg_color in log.game_messages:
        gui.terminal_set_color(255, msg_color)
        terminal.puts(bottom_panel_x, bottom_panel_y+msg_line, line)
        msg_line += 1

    gui.terminal_set_color(255, colors.white)

    terminal.puts(right_panel_x, bottom_panel_y, "Current Position:",
                  right_panel_width, bottom_panel_height-1,
                  terminal.TK_ALIGN_MIDDLE | terminal.TK_ALIGN_CENTER)
    terminal.puts(right_panel_x, bottom_panel_y, p.current_position,
                  right_panel_width, bottom_panel_height+1,
                  terminal.TK_ALIGN_MIDDLE | terminal.TK_ALIGN_CENTER)

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
terminal.set("""U+E250: assets/sword.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("""U+E300: assets/armor.png, size=16x16, align=center,
                resize=32x32""")
terminal.set("window: size=180x52, cellsize=auto, title='roguelike'")
terminal.composition(True)

# Initialize Game
player_fighter = objects.Fighter(hp=30, defense=2, power=5, recharge=20,
                                 death_function=player_death)
player = objects.GameObject('player', 1, 1, 0xE000, fighter=player_fighter)
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

inv = objects.Inventory()
player.inventory = inv

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

    for obj in dungeon_map.objects:
        if obj.ai:
            obj.ai.take_turn()
        if obj.fighter:
            obj.fighter.recharge()

    player.action = player_input(player, game)
    if player.action == 'exit':
        break

    terminal.delay(1000 // game.fps)
