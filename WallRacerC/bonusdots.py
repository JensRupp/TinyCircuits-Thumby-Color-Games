import engine_draw
import random

DOT_COUNT = 3  # number of bonus dots displayed
DOT_DISTANCE = 20  # minimum distance between dots
DOT_BORDER_DISTANCE = 10 # minimum distance from border for bonus points
DOT_TOLERANCE = 1  # how near the player needs to be to collect the bonus
BACKGROUND = engine_draw.black.value
ANIMATION = [engine_draw.yellow.value, engine_draw.red.value]

class BonusDots():
    def __init__(self, width: int, height: int):
        super().__init__()
        self.dots = []
        self.width = width
        self.height = height
        
        
# Add a bonus dot at random position but keep distance to other dots and player
    def add(self, allplayer):
        ok = False
        while not ok:
            ok = True
            x = random.randint(DOT_BORDER_DISTANCE, int(self.width) - DOT_BORDER_DISTANCE)
            y = random.randint(DOT_BORDER_DISTANCE, int(self.height) - DOT_BORDER_DISTANCE)

            # check distance to players
            for player in allplayer:
                player_x = player[0]
                player_y = player[1]
                if (
                    (x >= player_x - DOT_DISTANCE)
                    and (x <= player_x + DOT_DISTANCE)
                    and (y >= player_y - DOT_DISTANCE)
                    and (y <= player_y + DOT_DISTANCE)
                ):
                    ok = False
                    continue

            # check distance to other bonus
            for dot in self.dots:
                if (
                    (x >= dot[0] - DOT_DISTANCE)
                    and (x <= dot[0] + DOT_DISTANCE)
                    and (y >= dot[1] - DOT_DISTANCE)
                    and (y <= dot[1] + DOT_DISTANCE)
                ):
                    ok = False

        dot = [x, y]
        self.dots.append(dot)
        
    # Add inital bonus dots
    def init(self, allplayer):
        for c in range(DOT_COUNT):
            self.add(allplayer)
            
                # Draw one bonus dot at x,y location
    def draw(self, x, y, animation, screen):
        if animation == -1:
            color = BACKGROUND
        else:
            color = ANIMATION[int(animation // 5) % 2]

        # draw 3x3 dot
        for nx in range(x - 1, x + 2):
            screen.vline(nx, y - 1, 3, color)
            
    # Draw all bonus dots from the list
    def draw_all(self,animation, screen):
        for point in self.dots:
            self.draw(point[0], point[1], animation, screen)
            

    # Check if a bonus is at location x,y if yes remove it from screen and data
    def check(self, x, y, screen):
        hit = -1
        for index in range(len(self.dots)):
            point = self.dots[index]
            if (
                (x >= point[0] - DOT_TOLERANCE)
                and (x <= point[0] + DOT_TOLERANCE)
                and (y >= point[1] - DOT_TOLERANCE)
                and (y <= point[1] + DOT_TOLERANCE)
            ):
                # remove the bonus
                self.draw(point[0], point[1], -1, screen)
                del self.dots[index]
                return True
                
        return False
        
        
        
        