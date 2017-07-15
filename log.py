from bearlibterminal import terminal
import colors
import gui

game_messages = []

def message(new_msg, color=colors.white):
    if len(game_messages) == 6:
        del game_messages[0]
    game_messages.append((new_msg, color))
