import log
import colors
import objects
from tcod import libtcodpy as tcod
from bearlibterminal import terminal
import raycast

def cast_heal(target):
    if target.fighter.hp >= target.fighter.max_hp:
        log.message(target.name.capitalize() + ' is already at maximum health!',
                    colors.yellow)
        return 'cancelled'
    else:
        log.message('Your wounds begin to mend.', colors.red)
        target.fighter.heal(5)
        return 'used'


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
    proj = objects.Projectile(dx, dy, damage, range, aoe=False)
    return proj


def closest_monster(source, range):
    closest_enemy = None
    closest_dist = range + 1

    for obj in source.current_map.objects:
        if obj.fighter and obj.ai and (obj.x, obj.y) in source.visible:
            dist = source.distance_to(obj)
            if dist < closest_dist:
                closest_enemy = obj
                closest_dist = dist

    return closest_enemy


def lightning_bolt(source, spell_range, d_key):

    dx, dy = objects.direction_dict[d_key]
    affected_tiles = []
    for i in range(1, spell_range + 1):
        tx = source.x + (dx * i)
        ty = source.y + (dy * i)
        if source.current_map.terrain_blocked_at(tx, ty):
            affected_tiles.append((tx, ty, True))
            break
        else:
            if source.current_map.is_blocked_at(tx, ty):
                affected_tiles.append((tx, ty, True))
            else:
                affected_tiles.append((tx, ty, False))

    return affected_tiles


def fireball(source, spell_range, d_key):
    dx, dy = objects.direction_dict[d_key]
    icon = source.inventory.spell.icons[d_key]
    ball = objects.Projectile(dx, dy, 0, spell_range, aoe=True)
    explosion = objects.SpellEffect(name='explosion', spell_range=2,
                                    render_frames=7, damage=10,
                                    icons={'n' : 0xE388, 's' : 0xE388,
                                           'e' : 0xE388, 'w' : 0xE388,
                                           'se' : 0xE388, 'sw' : 0xE388,
                                           'ne' : 0xE388, 'nw' : 0xE388,
                                           'hit' : 0xE388}, charges=0,
                                           aoe_function=fireball_explode)
    fireball = objects.GameObject('fireball', source.x + dx, source.y + dy,
                                  icon, projectile=ball, spell=explosion,
                                  update_func=objects.update_ammo)
    return fireball


def fireball_explode(source, spell_range, d_key):
    damage = source.projectile.power
    affected_tiles = []

    obj = source
    w = obj.current_map.width
    h = obj.current_map.height

    for i in range(0, raycast.RAYS + 1, raycast.STEP):
        ax = raycast.sintable[i]
        ay = raycast.costable[i]

        x, y = obj.x, obj.y

        for z in range(spell_range):
            x += ax
            y += ay

            if x < 0 or y < 0 or x > w or y > h:
                break

            affected_tiles.append((int(round(x)), int(round(y)), True))

            if obj.current_map.tiles[int(round(x))][int(round(y))] == 0:
                break

    affected_tiles.append((obj.x, obj.y, True))

    return affected_tiles
