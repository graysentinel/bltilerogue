import log
import colors
import objects

def cast_heal(target):
    if target.fighter.hp >= target.fighter.max_hp:
        log.message(target.name.capitalize() + ' is already at maximum health!',
                    colors.yellow)
        return 'cancelled'
    else:
        log.message('Your wounds begin to mend.', colors.red)
        target.fighter.heal(5)


def sword_attack(source_x, source_y, d_key):
    target_tiles = []
    dx, dy = objects.direction_dict[d_key]
    target_x = source_x + dx
    target_y = source_y + dy
    target_tiles.append((target_x, target_y))
    return target_tiles


def axe_attack(source_x, source_y, d_key):
    target_tiles = []
    if d_key == 'n':
        dx1, dy1 = objects.direction_dict['n']
        dx2, dy2 = objects.direction_dict['ne']
        dx3, dy3 = objects.direction_dict['nw']
    elif d_key == 'ne':
        dx1, dy1 = objects.direction_dict['ne']
        dx2, dy2 = objects.direction_dict['n']
        dx3, dy3 = objects.direction_dict['e']
    elif d_key == 'e':
        dx1, dy1 = objects.direction_dict['e']
        dx2, dy2 = objects.direction_dict['ne']
        dx3, dy3 = objects.direction_dict['se']
    elif d_key == 'se':
        dx1, dy1 = objects.direction_dict['e']
        dx2, dy2 = objects.direction_dict['se']
        dx3, dy3 = objects.direction_dict['s']
    elif d_key == 's':
        dx1, dy1 = objects.direction_dict['se']
        dx2, dy2 = objects.direction_dict['s']
        dx3, dy3 = objects.direction_dict['sw']
    elif d_key == 'sw':
        dx1, dy1 = objects.direction_dict['s']
        dx2, dy2 = objects.direction_dict['sw']
        dx3, dy3 = objects.direction_dict['w']
    elif d_key == 'w':
        dx1, dy1 = objects.direction_dict['sw']
        dx2, dy2 = objects.direction_dict['w']
        dx3, dy3 = objects.direction_dict['nw']
    elif d_key == 'nw':
        dx1, dy1 = objects.direction_dict['w']
        dx2, dy2 = objects.direction_dict['nw']
        dx3, dy3 = objects.direction_dict['n']

    target_tiles.append((source_x + dx1, source_y + dy1))
    target_tiles.append((source_x + dx2, source_y + dy2))
    target_tiles.append((source_x + dx3, source_y + dy3))
    return target_tiles


def bow_attack(source, range, d_key, damage):
    dx, dy = objects.direction_dict[d_key]
    proj = objects.Projectile(dx, dy, damage, range)
    return proj
