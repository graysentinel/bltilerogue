import log
import colors

def cast_heal(target):
    if target.fighter.hp >= target.fighter.max_hp:
        log.message(target.name.capitalize() + ' is already at maximum health!',
                    colors.yellow)
        return 'cancelled'
    else:
        log.message('Your wounds begin to mend.', colors.red)
        target.fighter.heal(5)
