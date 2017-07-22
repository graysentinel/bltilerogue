from bearlibterminal import terminal
import tdl
import colors

def render_bar(x, y, total_width, name, value, maximum, bar_color):
    bar_width = int(float(value) / maximum * total_width)

    terminal_set_color(255, bar_color)
    for i in range(bar_width):
        terminal.put(x+i, y, 0x2588)
    terminal_set_color(255, colors.white)

def render_box(x, y, inv, key):
    # top line
    terminal.put(x, y, 0x250f)
    terminal.put(x + 1, y, 0x2501)
    terminal.put(x + 2, y, 0x2501)
    terminal.put(x + 3, y, 0x2501)
    terminal.put(x + 4, y, 0x2513)

    # middle line
    terminal.put(x, y + 1, 0x2503)
    terminal.put(x + 4, y + 1, 0x2503)

    # bottom line
    terminal.put(x, y + 2, 0x2517)
    terminal.put(x + 1, y + 2, 0x2501)
    terminal.put(x + 2, y + 2, 0x2501)
    terminal.put(x + 3, y + 2, 0x2501)
    terminal.put(x + 4, y + 2, 0x251b)

    # item x = x + 2
    # item y = y + 1

    terminal.put(x + 2, y + 1, inv.get_item_icon(key))
    terminal.puts(x + 6, y + 1, inv.get_item_name(key))

def terminal_set_color(alpha, color):
    color_argb = colors.convert_argb(alpha, color)
    terminal.color(terminal.color_from_argb(a=color_argb[0], r=color_argb[1],
                   g=color_argb[2], b=color_argb[3]))

def terminal_reset_color():
    terminal.color("white")

def tile_dimmer(x, y, alpha):
    terminal_set_color(alpha, colors.black)
    terminal.put(x*4, y*2, 0xE050)
    terminal_reset_color()

def light_effect(x, y, light_alpha, light_color):
    terminal_set_color(light_alpha, light_color)
    terminal.put(x*4, y*2, 0xE050)
    terminal_reset_color()
