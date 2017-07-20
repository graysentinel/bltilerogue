from bearlibterminal import terminal
import tdl
import objects
import maps
import gui
import colors
import log

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
            if key == terminal.TK_LEFT:
                player_move_or_attack(p, objects.west)
            elif key == terminal.TK_RIGHT:
                player_move_or_attack(p, objects.east)
            elif key == terminal.TK_UP:
                player_move_or_attack(p, objects.north)
            elif key == terminal.TK_DOWN:
                player_move_or_attack(p, objects.south)
            else:
                return 'no-turn'


def player_move_or_attack(p, direction):

    target = None
    x, y = p.move(direction)
    for obj in p.current_map.objects:
        if obj.fighter and (obj.x == x and obj.y == y):
            target = obj
            break

    if target is not None:
        p.fighter.attack(target)
    else:
        if not p.current_map.is_blocked_at(x, y):
            p.x, p.y = x, y
            # print("Player Position: ({}, {})".format(p.x, p.y))
            p.camera.move(direction)
            # p.current_map.fov_recompute = True


def player_death(p):
    log.message('You died!', colors.red)
    p.alive = False
    p.icon = 0xE150


def render(p, gm):

    terminal.clear()
    #calculate field of view for all rendering below
    #if map.fov_recompute:
        #map.fov_recompute = False
    visible_tiles = tdl.map.quickFOV(p.x, p.y, p.current_map.is_visible_tile,
                                     fov=p.fov_algo,
                                     radius=p.sight_radius,
                                     lightWalls=p.fov_light_walls)

    light_source_tiles = []

    ''' Render Object Layer '''
    terminal.layer(2)
    for o in p.current_map.objects:
        if (o.x, o.y) in visible_tiles:
            o.draw(p.camera)
        if o.light_source:
            for x, y in o.light_source.tiles_lit:
                light_source_tiles.append((x, y, o.light_source.color))

    ''' Render Map Layer '''
    terminal.layer(1)
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

            #print(light_source_tiles)
            for lx, ly, lcolor in light_source_tiles:
                if lx == tx and ly == ty:
                    gui.terminal_set_color(200, lcolor)
                    terminal.put(x*4, y*2,
                                 maps.terrain_types[tile].icon_seen)
                    gui.terminal_reset_color()

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

    gui.render_bar(right_panel_x + 2, right_panel_y + 1, right_panel_width-4,
                   'attack power', p.fighter.power_meter, 100,
                   colors.darker_red)

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
terminal.set("window: size=180x52, cellsize=auto, title='roguelike'")

# Initialize Game
player_fighter = objects.Fighter(hp=30, defense=2, power=5, recharge=20,
                                 death_function=player_death)
player = objects.GameObject('player', 1, 1, 0xE000, fighter=player_fighter)
dungeon_map = maps.DungeonMap(100, 100)
dungeon_map.make_map(player)
dungeon_map.objects.append(player)

player.current_map = dungeon_map
player.action = None
player.fov_algo = 'BASIC'
player.fov_light_walls = True
player.object_id = 'p1'
player.alive = True
player.sight_radius = 5

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
