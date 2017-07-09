from bearlibterminal import terminal
import tdl
import objects
import maps

class GameMaster:
    def __init__(self, game_state):
        self.game_state = game_state
        self.players = []
        self.action_queue = []
        self.fps = 25


def player_input(p, gm):

    if gm.game_state == 'playing':

        key = None
        while terminal.has_input():
            key = terminal.read()

        if key in (terminal.TK_CLOSE, terminal.TK_ESCAPE):
            return 'exit'

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
        if obj.x == x and obj.y == y:
            target = obj
            break

    if target is not None:
        print('The ' + target.name + ' chuckles evilly.')
    else:
        if not p.current_map.is_blocked_at(x, y):
            p.x, p.y = x, y
            p.current_map.fov_recompute = True


def render(map, gm):

    # get player object
    p = None
    for obj in map.objects:
        if obj.name == 'player':
            p = obj

    #calculate field of view for all rendering below
    #if map.fov_recompute:
        #map.fov_recompute = False
    visible_tiles = tdl.map.quickFOV(p.x, p.y, map.is_visible_tile,
                                     fov=p.fov_algo,
                                     radius=map.default_torch_radius,
                                     lightWalls=p.fov_light_walls)

    ''' Render Object Layer '''
    terminal.layer(2)
    for o in map.objects:
        if (o.x, o.y) in visible_tiles:
            o.draw()

    ''' Render Map Layer '''

    terminal.layer(1)
    for y in range(map.height):
        for x in range(map.width):
            visible = (x, y) in visible_tiles
            tile = map.tiles[x][y]
            if not visible:
                if map.tiles_explored[x][y] == 1:
                    terminal.put(x*2, y,
                                 maps.terrain_types[tile].icon_unseen)
                else:
                    terminal.put(x*2, y, 0xE050)
            else:
                terminal.put(x*2, y, maps.terrain_types[tile].icon_seen)
                map.tiles_explored[x][y] = 1

    ''' Render GUI '''
    terminal.layer(0)
    terminal.color("white")

    right_panel_x = map.width * 2
    right_panel_y = 1
    right_panel_width = terminal.state(terminal.TK_WIDTH) - map.width*2
    right_panel_height = terminal.state(terminal.TK_HEIGHT) - map.height

    bottom_panel_x = 1
    bottom_panel_y = map.height + 1
    bottom_panel_width = terminal.state(terminal.TK_WIDTH) - right_panel_width
    bottom_panel_height = terminal.state(terminal.TK_HEIGHT) - bottom_panel_y

    for y in range(0, terminal.TK_HEIGHT-bottom_panel_height):
        terminal.put(right_panel_x, y, 0x2588)

    terminal.puts(right_panel_x, right_panel_y, "GUI Here",
                  right_panel_width, right_panel_height,
                  terminal.TK_ALIGN_TOP | terminal.TK_ALIGN_CENTER)

    for x in range(0, terminal.TK_WIDTH):
        terminal.put(x, bottom_panel_y-1, 0x2588)
    terminal.printf(bottom_panel_x, bottom_panel_y+1, "Bottom Panel Here")

    terminal.puts(right_panel_x, bottom_panel_y, "Current Position:",
                  right_panel_width, bottom_panel_height-1,
                  terminal.TK_ALIGN_MIDDLE | terminal.TK_ALIGN_CENTER)
    terminal.puts(right_panel_x, bottom_panel_y, p.current_position,
                  right_panel_width, bottom_panel_height,
                  terminal.TK_ALIGN_MIDDLE | terminal.TK_ALIGN_CENTER)

    terminal.refresh()


def current_layer():
    return terminal.state(terminal.TK_LAYER)

# Initialize Window
terminal.open()
terminal.set("""U+E000: assets/rogue.png, size=16x16,
             align=center""")
terminal.set("""U+E050: assets/floors.png, size=16x16,
             align=center""")
terminal.set("""U+E060: assets/walls.png, size=16x16,
             align=center""")
terminal.set("""U+E070: assets/doors.png, size=16x16,
             align=center""")
terminal.set("""U+E100: assets/basic-monsters.png, size=16x16,
             align=center""")
terminal.set("window: size=180x52, cellsize=auto, title='roguelike'")

# Initialize Game
player_fighter = objects.Fighter(hp=30, defense=2, power=5)
player = objects.GameObject('player', 1, 1, 0xE000, fighter=player_fighter)
dungeon_map = maps.DungeonMap(75, 45)
dungeon_map.make_map(player)
dungeon_map.objects.append(player)

player.current_map = dungeon_map
player.action = None
player.fov_algo = 'BASIC'
player.fov_light_walls = True
player.object_id = 'p1'

game = GameMaster('playing')

# Main Game Loop
while True:
    render(dungeon_map, game)

    terminal.layer(2)
    for o in dungeon_map.objects:
        o.clear()

    for obj in dungeon_map.objects:
        if obj.ai:
            obj.ai.take_turn()

    player.action = player_input(player, game)
    if player.action == 'exit':
        break

    terminal.delay(1000 // game.fps)
