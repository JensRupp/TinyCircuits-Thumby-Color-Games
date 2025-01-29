import random
import engine_io
import engine_draw

EXPLOSION_BITS = 72  # number of pixels in the explosion
EXPLOSION_STEPS = 40  # number of steps the explosion runs
EXPLOSION_RUMBLE = 0.4 # rumble intensity during explosion

BACKGROUND = engine_draw.black.value
EXPLOSION = engine_draw.red.value

class Explosion():
    def __init__(self, width: int, height: int):
        super().__init__()
        self.bits = []
        self.width = width
        self.height = height
        self.step = 0
        
    def add(self, x, y):
        for count in range(EXPLOSION_BITS):
            # x,y x speed, y speed
            bit = [
                x,
                y,
                (random.randint(0, 20) - 10) / 20,
                (random.randint(0, 20) - 10) / 20,
            ]
            self.bits.append(bit)
        self.fix()            
        engine_io.rumble(EXPLOSION_RUMBLE)
        self.step = EXPLOSION_STEPS
        
    def clear(self, screen):
        for bit in self.bits:
            screen.pixel(int(bit[0]), int(bit[1]), BACKGROUND)
        self.bits = []
        
    #prevent bits to clear outer wall    
    def fix(self):
        for bit in self.bits:
            if bit[0] < 1:
                bit[0] = 1
            if bit[0] >= self.width - 1:
                bit[0] = self.width - 2

            if bit[1] < 1:
                bit[1] = 1
            if bit[1] >= self.height - 1:
                bit[1] = self.height - 2
        
    def move(self, screen):
        if self.step > 0:
            # remove from current position
            for bit in self.bits:
                screen.pixel(int(bit[0]), int(bit[1]), BACKGROUND)
                
            # move bits to new position
            for bit in self.bits:
                bit[0] = bit[0] + bit[2]
                bit[1] = bit[1] + bit[3]
            self.fix()    

            # draw at new position
            for bit in self.bits:
                screen.pixel(int(bit[0]), int(bit[1]), EXPLOSION)
                
            self.step -= 1
            if self.step == 0:
                engine_io.rumble(0)
                self.clear(screen)
                return True
            else:
              return False
        else:
            return False
        
