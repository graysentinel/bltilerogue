from bearlibterminal import terminal

class GameObject:
    def __init__(self, name, x, y, icon, blocks=False, ai=None):
        self.name = name
        self.x = x
        self.y = y
        self.icon = icon
        self.blocks = blocks
        self.ai = ai
        if self.ai:
            self.ai.owner = self
            
        self.object_id = None

    def draw(self):
        terminal.put(self.x*2, self.y, self.icon)

    def clear(self):
        terminal.put(self.x*2, self.y, ' ')

    def move(self, direction):
        tgt_x = self.x + direction.goal_x
        tgt_y = self.y + direction.goal_y

        return(tgt_x, tgt_y)

    @property
    def current_position(self):
        return "(" + str(self.x) + "," + str(self.y) + ")"


class Direction:
    def __init__(self, goal_x, goal_y):
        self.goal_x = goal_x
        self.goal_y = goal_y

north = Direction(0, -1)
south = Direction(0, 1)
east = Direction(1, 0)
west = Direction(-1, 0)
northeast = Direction(1, -1)
northwest = Direction(-1, -1)
southeast = Direction(1, 1)
southwest = Direction(-1, 1)

directions = [north, south, east, west, northeast, northwest, southeast,
              southwest]
