from bearlibterminal import terminal
import tdl
import objects
import maps

def player_input(p):
    key = terminal.read()

    if key in (terminal.TK_CLOSE, terminal.TK_ESCAPE):
        return 'exit'

    if key == terminal.TK_LEFT:
        p.move(objects.west, p.current_map)
        p.current_map.fov_recompute = True
    elif key == terminal.TK_RIGHT:
        p.move(objects.east, p.current_map)
        p.current_map.fov_recompute = True
    elif key == terminal.TK_UP:
        p.move(objects.north, p.current_map)
        p.current_map.fov_recompute = True
    elif key == terminal.TK_DOWN:
        p.move(objects.south, p.current_map)
        p.current_map.fov_recompute = True

def render(map):

    p = None
    for obj in map.objects:
        if obj.name == 'player':
            p = obj

    if map.fov_recompute:
        map.fov_recompute = False
        visible_tiles = tdl.map.quickFOV(p.x, p.y, map.is_visible_tile,
                                         fov=p.fov_algo,
                                         radius=map.default_torch_radius,
                                         lightWalls=p.fov_light_walls)

        ''' Render Object Layer '''
        terminal.layer(2)
        #print('Render Objects on: ' + str(current_layer()))
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
        terminal.puts(right_panel_x, right_panel_y, "GUI Starts Here",
                      right_panel_width, right_panel_height, terminal.TK_ALIGN_TOP |
                      terminal.TK_ALIGN_CENTER)

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

player = objects.GameObject('player', 1, 1, 0xE000)
dungeon_map = maps.DungeonMap(75, 45)
dungeon_map.make_map(player)
dungeon_map.objects.append(player)
player.current_map = dungeon_map

player.fov_algo = 'BASIC'
player.fov_light_walls = True

while True:
    render(dungeon_map)

    terminal.layer(2)
    #print('Clear Objects on: ' + str(current_layer()))
    for o in dungeon_map.objects:
        o.clear()

    key_in = player_input(player)
    if key_in == 'exit':
        break
