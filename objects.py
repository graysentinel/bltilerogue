from bearlibterminal import terminal

class GameObject:
    def __init__(self, name, x, y, icon, blocks=False):
        self.name = name
        self.x = x
        self.y = y
        self.icon = icon
        self.blocks = blocks

    def draw(self):
        terminal.put(self.x*2, self.y, self.icon)

    def clear(self):
        terminal.put(self.x*2, self.y, ' ')

    def move(self, direction, map):
        tgt_x = self.x + direction.goal_x
        tgt_y = self.y + direction.goal_y

        if not map.is_blocked_at(tgt_x, tgt_y):
            self.x = tgt_x
            self.y = tgt_y
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
