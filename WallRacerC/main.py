import os
import engine_main
import engine
from engine_nodes import EmptyNode, Rectangle2DNode, CameraNode, Text2DNode, Sprite2DNode
import engine_io
import gc
import framebuf
import engine_draw
import time
import random
from engine_math import Vector2
from engine_resources import FontResource, TextureResource
import math
import engine_link
import engine_save
import json
from gaclib import options
from gaclib import helper
from gaclib import highscore
from gaclib import multiplayer
from gaclib import logger

# Const Definitions
GAME_NAME = "WallRacer"
VERSION = "V1.5"
SCREEN_WIDTH = 128
SCREEN_HEIGHT = 128
VIRTUAL_WIDTH = [int(SCREEN_WIDTH), int(SCREEN_WIDTH * 1.5), int(SCREEN_WIDTH * 2)] 
VIRTUAL_HEIGHT = [int(SCREEN_HEIGHT), int(SCREEN_HEIGHT * 1.5), int(SCREEN_HEIGHT * 2) ]
BONUS_FACTOR = 20  # points for collecting a bonus dot multiplied by speed
BONUS_DISTANCE = 20  # minimum distance between dots
BONUS_COUNT = 3  # number of bonus dots displayed
BONUS_TOLERANCE = 1  # how near the player needs to be to collect the bonus
BONUS_BORDER_DISTANCE = 10 # minimum distance from border for bonus points 
EXPLOSION_BITS = 72  # number of pixels in the explosion
EXPLOSION_STEPS = 20  # number of steps the explosion runs
EXPLOSION_RUMBLE = 0.4 # rumble intensity during explosion
POINTS_WON = 1000  # extra points for winning
#BOOST_COOLDOWN = 80  # number of pixels to wait for next boost
BOOST_COOLDOWN = 20
BOOST_TIME = 40  # number of pixels to boost
BOOST_SPEED = 4  # increase of speed during boost
BOOST_RUMBLE = 0.2  # rumble intensity during boost
# map direction to offsets
PLAYERXADD = [1, 0, -1, 0]  # mapping of direction to x add
PLAYERYADD = [0, 1, 0, -1]  # mapping of direction to y add
START_BORDER_DISTANCE = 30
FPSAVERAGECOUNT = 10

# pages
PAGE_QUIT = 0
PAGE_TITLE = 1
PAGE_GAME = 2
PAGE_OPTIONS = 3
PAGE_WAITFORPLAYER = 4
PAGE_HIGHSCORE = 5
PAGE_ENTERHIGHSCORE = 6
PAGE_TEST = 7

# map engine colors to framebuffer
BLACK = engine_draw.black.value
GREEN = engine_draw.green.value
WHITE = engine_draw.white.value
RED = engine_draw.red.value
YELLOW = engine_draw.yellow.value
PINK = engine_draw.pink.value
GREY = engine_draw.darkgrey.value
GREYL = engine_draw.lightgrey.value
BLUE = engine_draw.blue.value
DARKGREEN = engine_draw.darkgreen.value
GREENYELLOW = engine_draw.greenyellow.value

# used colors
BACKGROUND = BLACK
FRAME1 = WHITE
FRAME2 = RED
#PLAYER_COLOR=[GREEN, BLUE, RED, YELLOW, PINK, GREY]

#LIGHT MEDIUM DARK
#GREEN, BLUE, RED, ORANGE, VIOLET, TURQUOISE
PLAYER_COLOR=[[0xbff7, 0x8c7f, 0xfcd3, 0xfead, 0xfa9f, 0x1ffc], [0x07e0, 0x001F, 0xF800,  0xFDA0, 0xb817, 0x05b4], [0x0540, 0x18f2, 0xa800, 0xbc40, 0x9813, 0x034c]]

EXPLOSION = RED
ANIMATION = [YELLOW, RED]

def lighter(color):
    r = color >> 11
    r += 5
    if r > 31:
        r = 31
    
    g = (color >> 5) & 0b00111111
    g  += 10
    if g > 63:
        g = 63
    
    b = color & 0b00011111
    b += 5
    if b > 31:
        b = 31
        
    c = (r << 11) + (g << 5) + b
    return c
    
    
    
log = logger.log("/Games/WallRacerC/wallracer.log")
#log.start()
log.info("Start")


def print_memory_usage():
    gc.collect()
    free_memory = gc.mem_free()
    allocated_memory = gc.mem_alloc()
    total_memory = free_memory + allocated_memory
    print(f"Total Memory: {total_memory} bytes")
    print(f"Allocated Memory: {allocated_memory} bytes")
    print(f"Free Memory: {free_memory} bytes")
    print()

# Initialization
random.seed(time.ticks_ms())

camera = CameraNode()

# init fonts
os.chdir("/Games/WallRacerC")
font16 = FontResource("font16.bmp")
font6 = FontResource("font6x8.bmp")
logo = TextureResource("WallRacerCLogo.bmp")

def initHighscore():
    showtitle = helper.Text("Highscore", font16, Vector2(1.5, 1.5), GREEN )
    showsubtitle = helper.Format(font16, Vector2(1, 1), GREEN)
    showfooter = helper.Text("U/D Scroll A/B Exit",font6,Vector2(1, 1),YELLOW)
    showtable = helper.Format(font16, Vector2(1, 1), WHITE)
    letter = helper.Format(font16, Vector2(3, 3), GREY)
    entertitle = helper.Text("New\nHighscore", font16, Vector2(1.5, 1.5), GREEN )
    enterfooter = helper.Text("L/R Move Selection\nU/D Change Letter\nA/B Confirm",font6,Vector2(1, 1),YELLOW)
    
    score = highscore.highscore(showtitle, showsubtitle, showfooter, showtable, entertitle, enterfooter, letter, WHITE, 10, "wallracer.data")

    #register all possible highscore ids
    for speed in range(1,11):
        for arena in range (1,4):
            for bonus in range (1,3):
                id = "S"+str(speed)+"A"+str(arena)+"B"+str(bonus)
                name = id
                score.register(id, name, 100, "GAC")
            
    return score

class Settings():
    def __init__(self):
        #empty data sets defaults
        self.set({})
        
    def get(self):
        data = {}
        #these names must match the definitions in wallracer.options
        data["speed"] = self.speed
        data["link"] = self.link
        data["player1t"] = self.player1t
        data["player2t"] = self.player2t
        data["arena"] = self.arena
        data["arenasmall"] = self.arenasmall
        data["boost"] = self.boost
        data["bonus"] = self.bonus
        data["showfps"] = self.showfps
        return data
    
    def set(self, data):
        self.speed = data.get("speed", 5)
        self.link = data.get("link", False)
        self.player1t = data.get("player1t",1)
        self.player2t = data.get("player2t",1)
        self.arena = data.get("arena",3)
        self.arenasmall = data.get("arenasmall",1)
        self.boost = data.get("boost",1)
        self.bonus = data.get("bonus",1)
        self.showfps = data.get("showfps", False)
        
    def highscore_id(self):
        #highscore for now only on single player
        if (not self.link) and (self.player1t == 1):
            id = "S"+str(self.speed)+"A"+str(self.arena)+"B"+str(self.bonus)    
        else:    
            id = ""
        return id    
        
        
    def save(self):
        engine_save.set_location("wallracer.data")    
        data = self.get()
        data_json = json.dumps(data)
        engine_save.save("options", data_json)
    
    def load(self):
        engine_save.set_location("wallracer.data")
        data_json = engine_save.load("options", json.dumps(self.get()))
        data = json.loads(data_json)
        self.set(data)

# Global Settings
settings = Settings()
settings.load()

score = initHighscore()

# Add a bonus dot at random position but keep distance to other dots and player
def addBonus(multi):
    ok = False
    while not ok:
        ok = True
        x = random.randint(BONUS_BORDER_DISTANCE, multi.state.width - BONUS_BORDER_DISTANCE)
        y = random.randint(BONUS_BORDER_DISTANCE, multi.state.height - BONUS_BORDER_DISTANCE)

        # check distance to players
        for player in range(0,multi.count):
            player_x = multi.read_player("x", player)
            player_y = multi.read_player("y", player)
            if (
                (x >= player_x - BONUS_DISTANCE)
                and (x <= player_x + BONUS_DISTANCE)
                and (y >= player_y - BONUS_DISTANCE)
                and (y <= player_y + BONUS_DISTANCE)
            ):
                ok = False

        # check distance to other bonus
        for point in multi.state.bonus:
            if (
                (x >= point[0] - BONUS_DISTANCE)
                and (x <= point[0] + BONUS_DISTANCE)
                and (y >= point[1] - BONUS_DISTANCE)
                and (y <= point[1] + BONUS_DISTANCE)
            ):
                ok = False

    point = [x, y]
    multi.state.bonus.append(point)


# Add inital bonus
def initBonus(multi):
    multi.state.bonus.clear()
    for c in range(BONUS_COUNT):
        addBonus(multi)


# Draw one bonus dot at x,y location
def drawBonus(x, y, animation, state):
    if animation == -1:
        color = BACKGROUND
    else:
        color = ANIMATION[int(animation // 5) % 2]

    # draw 3x3 dot
    for nx in range(x - 1, x + 2):
        state.screen.vline(nx, y - 1, 3, color)


# Draw all bonus dots from the list
def drawBonusList(animation, state):
    for point in state.bonus:
        drawBonus(point[0], point[1], animation, state)


# Check if a bonus is at location x,y if yes remove it from screen and return the index in the list
def checkBonus(x, y, state):
    hit = -1
    for index in range(len(state.bonus)):
        point = state.bonus[index]
        if (
            (x >= point[0] - BONUS_TOLERANCE)
            and (x <= point[0] + BONUS_TOLERANCE)
            and (y >= point[1] - BONUS_TOLERANCE)
            and (y <= point[1] + BONUS_TOLERANCE)
        ):
            # remove the bonus
            drawBonus(point[0], point[1], -1, state)
            hit = index
    return hit

# draw a frame with alternating colors
def drawFrame(screen, width: int, height: int):
    screen.rect(0, 0, width , height , FRAME1)

    lw = int(SCREEN_WIDTH / 4)
    c = int((width / (lw * 2)) )
    for step in range(c):
        screen.hline(lw + step * lw * 2, 0, lw, FRAME2)
        screen.hline(lw + step * lw * 2, height - 1, lw, FRAME2)

    w = int(SCREEN_HEIGHT / 4)
    c = int((height / (lw * 2)) )
    for step in range(c):
        screen.vline(0, lw + step * lw * 2, lw, FRAME2)
        screen.vline(width - 1, lw + step * lw * 2, lw, FRAME2)

#display the bonus
def displayBonus(points, state):
    state.bonus1 = Text2DNode(
        position=Vector2(0, -20),
        text="Bonus!",
        font=font16,
        line_spacing=1,
        color=WHITE,
        scale=Vector2(2, 2),
        layer = 100
    )

    state.bonus2 = Text2DNode(
        position=Vector2(0, 20),
        text=str(points),
        font=font16,
        line_spacing=1,
        color=WHITE,
        scale=Vector2(2, 2),
        layer = 100
    )
    #display for a short time
    state.sleep =  engine.fps_limit() // 2


class GameState():
    def __init__(self, screen):
        self.width = 0
        self.height = 0
        self.won = -1
        self.screen = screen
        self.arena = None
        self.speed = 0 #set from settings
        # for explosions
        self.bits = []
        self.explosion = 0
        # for bonus points
        self.hasbonus = False
        self.bonus = []
        
        # for bonus point display
        self.sleep = 0
        self.bonus1 = None
        self.bonus2 = None
        
        #for identify
        self.idplayer = [None, None, None]

        #for boost
        self.hasboost = False
        self.boost = 0
        
        #for player control
        self.control = []
    
        
def control1():
    bl = engine_io.LB.is_just_pressed
    br = engine_io.RB.is_just_pressed
    bb = engine_io.B.is_just_pressed
    return bl,br,bb

def control2():
    bl = engine_io.UP.is_just_pressed
    br = engine_io.DOWN.is_just_pressed
    bb = engine_io.LB.is_just_pressed
    return bl,br,bb

def control3():
    bl = engine_io.B.is_just_pressed
    br = engine_io.A.is_just_pressed
    bb = engine_io.RB.is_just_pressed
    return bl,br,bb

def control4():
    bl = engine_io.UP.is_just_pressed
    br = engine_io.DOWN.is_just_pressed
    bb = False
    return bl,br,bb

def control5():
    bl = engine_io.B.is_just_pressed
    br = engine_io.A.is_just_pressed
    bb = False
    return bl,br,bb

def control6():
    bl = engine_io.RB.is_just_pressed
    br = engine_io.LB.is_just_pressed
    bb = False
    return bl,br,bb

def cbidentifyplayers(multi, create):
    if create:
        if multi.is_host():
            playeradd = 0
        else:
            playeradd = multi.local_count
        for player in range(0, multi.local_count):
            if multi.local_count == 1:
                rotation = 0
                if multi.state.hasboost:
                    buttons="LB/RB/B"
                else:  
                    buttons="LB/RB"
            elif player == 0:
                rotation = - math.pi / 2
                if multi.state.hasboost:
                    buttons="U/D/LB"
                else: 
                    buttons="U/D"
            elif player == 1:
                rotation = math.pi / 2
                if multi.state.hasboost:
                    buttons="B/A/RB"
                else:  
                    buttons="B/A"
            elif player == 2:
                rotation = - math.pi
                buttons="RB/LB"
        
            multi.state.idplayer[player] = Text2DNode(
                                position=Vector2(0, 0),
                                text="Player "+str(player+1+playeradd)+" "+buttons,
                                font=font6,
                                line_spacing=1,
                                color=PLAYER_COLOR[1][player+playeradd],
                                scale=Vector2(1, 1),
                                rotation= rotation
                                )
            multi.add_child(multi.state.idplayer[player])
            
            
            if multi.local_count == 1:
                helper.align_top(multi.state.idplayer[player])
            elif player == 0:
                helper.align_left(multi.state.idplayer[player], - 32)
            elif player == 1:
                helper.align_right(multi.state.idplayer[player], - 32)
            elif player == 2: 
                helper.align_top(multi.state.idplayer[player])
            

    else:
        for player in range(0, multi.local_count):
            multi.state.idplayer[player].mark_destroy()
        


# initialize the synced data on the host
def cbinitgame(multi):
    multi.write("speed", multi.state.speed)
    
    for player in range (0, multi.count):
        if multi.count == 1:
            startpos = random.randint(0, 3)
        elif multi.count  == 2:
            startpos = random.randint(player*2, player*2+1)
        else:
            startpos = player
       
        if startpos == 0:
            # topleft
            x = START_BORDER_DISTANCE
            y = START_BORDER_DISTANCE
            d = 0
        elif startpos == 1:
            # bottomleft
            x = START_BORDER_DISTANCE
            y = multi.state.height - START_BORDER_DISTANCE
            d = 0
        elif startpos == 2:
            #topright
            x = multi.state.width - START_BORDER_DISTANCE
            y = START_BORDER_DISTANCE
            d = 2
        elif startpos == 3:
            #bottomright
            x = multi.state.width - START_BORDER_DISTANCE
            y = multi.state.height - START_BORDER_DISTANCE
            d = 2
        elif startpos == 4:
            #bottomright
            x = 64 #multi.state.width // 2
            y = START_BORDER_DISTANCE
            d = 1
        elif startpos == 5:
            #bottomright
            x = 64 #multi.state.width // 2
            y = multi.state.height - START_BORDER_DISTANCE
            d = 3

        multi.write_player("x", x, player)
        multi.write_player("y", y, player)
        multi.write_player("d", d, player)
        
    if multi.state.hasbonus:       
        initBonus(multi)
    


def cbinitplayer(multi, player):
    #set speed to lowest of all players
    hostspeed = multi.read("speed")
    
    if multi.state.speed < hostspeed:
        hostspeed = multi.state.speed
        multi.write("speed",hostspeed)
    throttle = 11 - hostspeed
    
    multi.write_player("t", throttle, player)
    multi.write_player("c", 0, player)
    multi.write_player("b", 0, player)
    multi.write_player("p", 0, player)
    
       
def cbplayer(multi, player):
    if multi.state.sleep > 0:
        multi.state.sleep -= 1
        
        if multi.state.sleep < 1 :
            multi.state.sleep = 0 # fix strange rounding error
            multi.state.bonus1.mark_destroy()
            multi.state.bonus2.mark_destroy()
    else:
        x = multi.read_player("x", player)
        y = multi.read_player("y", player)
        direction = multi.read_player("d", player)
        throttle = multi.read_player("t", player)
        crash = multi.read_player("c", player)
        boost = multi.read_player("b", player) - BOOST_COOLDOWN
        points = multi.read_player("p", player)
         
        # only move if not crashed
        if (crash == 0):
            lb,rb,bb = multi.state.control[player]()
            if lb:
                direction = (direction - 1) % 4
                multi.write_player("d", direction, player)

            if rb:
                direction = (direction + 1) % 4
                multi.write_player("d", direction, player)
                
            if multi.state.hasboost and (boost == 0) and bb:
                boost = BOOST_TIME
                throttle -= BOOST_SPEED
                #limit throttle to max speed
                if throttle < 1:
                    throttle = 1
                multi.write_player("t", throttle, player)
                multi.write_player("b", boost + BOOST_COOLDOWN , player)
                
                if multi.local_count == 1:
                    engine_io.indicator(engine_draw.red)    
                               
            if multi.counter % throttle == 0:
                if multi.state.hasboost:
                    if boost < 0:
                        boost += 1
                        if boost == 0:
                            if multi.local_count == 1:
                                engine_io.indicator(engine_draw.green)
                        multi.write_player("b", boost + BOOST_COOLDOWN , player)
                    elif boost >  0:
                        boost -= 1
                        if boost == 0:
                            speed = multi.read("speed")
                            throttle = 11 - speed
                            boost = -BOOST_COOLDOWN
                            multi.write_player("t", throttle, player)
                            if multi.local_count == 1:
                                engine_io.indicator(engine_draw.blue)
                        multi.write_player("b", boost + BOOST_COOLDOWN , player)        
                
                
                x += PLAYERXADD[direction]
                y += PLAYERYADD[direction]
                multi.write_player("x", x, player)
                multi.write_player("y", y, player)
                
                points += 1

                if multi.state.hasbonus: 
                    hit = checkBonus(x, y, multi.state)
                    if hit >= 0:
                        # if hit remove the existing bonus and add a new one
                        del multi.state.bonus[hit]
                        addBonus(multi)
                        speed = multi.read("speed")
                        bonus_points = speed * BONUS_FACTOR
                        points += points
                        displayBonus(bonus_points, multi.state)

                if multi.state.screen.pixel(x, y) != BACKGROUND:
                    multi.write_player("c", 1, player)

                multi.write_player("p", points, player)

#not used
def cbwork(multi):
    pass


def cbdisplay(multi):
    if multi.is_host():
        this = 0
    else:
        this = 1

    #draw player
    for player in range(0, multi.count):
        x = multi.read_player("x", player)
        y = multi.read_player("y", player)
        c = multi.read_player("c", player)
        
        if c == 0:
            if multi.state.hasboost:
                b = multi.read_player("b", player) - BOOST_COOLDOWN
                if b < 0:
                    color = 2
                elif b > 0:
                    color = 0
                else:
                    color = 1
                #print("P "+str(player)+" B" +str(b)+" C "+str(color)) 
            else:
                color = 1
            
                
            multi.state.screen.pixel(x, y, PLAYER_COLOR[color][player])
        elif c == 1:
            addexplosion(x,y, multi.state)
            multi.write_player("c", 2, player)
        #center on this player
        if multi.state.width > SCREEN_WIDTH:
            if player == this:
                screenx = SCREEN_WIDTH - x
                screeny = SCREEN_HEIGHT - y
                multi.state.arena.position = Vector2(screenx, screeny)

    if multi.state.hasbonus:
        drawBonusList(multi.counter, multi.state)


    if multi.state.explosion > 0:
        moveexplosion(multi.state)
        multi.state.explosion -= 1

        if multi.state.explosion == 0:
            engine_io.rumble(0)
            clearexplosion(multi.state)
            
            #count active players
            if multi.count > 1:
                active = 0
                for player in range(0, multi.count):
                    if multi.read_player("c", player) == 0:
                        multi.state.won = player
                        active+=1
                #for multiplayer game stop when 1 player is left        
                if active < 2:        
                    time.sleep(0.5)        
                    multi.docancel()
            else:
                #for singleplayer always stop after explosion
                multi.state.won = 0
                time.sleep(0.5)        
                multi.docancel()
                

def initScreen(width: int, height: int):
    texture = TextureResource(int(width), int(height),0,16)
    virtual_screen = framebuf.FrameBuffer(texture.data, texture.width, texture.height, framebuf.RGB565)
    
    # Clear virtual screen
    virtual_screen.fill(BACKGROUND)
    # Add the frame
    drawFrame(virtual_screen, width, height)
    arena = Sprite2DNode(texture=texture)
    return virtual_screen, arena
    
def finishScreen(arena):    
    arena.mark_destroy()

fpscount = FPSAVERAGECOUNT
fpssum = 0

def addFPS():
    global settings
    node = None
    if settings.showfps:
        node =  Text2DNode(
          position=Vector2(0, 0),
          text="FPS",
          font=font16,
          line_spacing=1,
          color=YELLOW,
          scale=Vector2(1, 1),
          layer=100
        )
        helper.align_top(node)
        helper.align_left(node)
    return node    
        
def updateFPS(fpsnode):
    global fpscount
    global fpssum 
    global setttings
    
    if settings.showfps:
        fps = engine.get_running_fps()
        fpssum += fps
        fpscount -= 1
        if fpscount == 0:
            fpsnode.text = str(int(fpssum // FPSAVERAGECOUNT))
            #helper.align_left(fpsnode)
            fpssum = 0
            fpscount = FPSAVERAGECOUNT

def playGame():
    global settings
    
    engine.fps_limit(120)

    if settings.link:
        devicecount = 2
        localcount = settings.player2t
    else:
        devicecount = 1
        localcount = settings.player1t

    multi = multiplayer.MultiplayerNode(devicecount, localcount)
    multi.log = log
    multi.text_connecting = helper.Text("Connecting", font16,Vector2(1, 1), WHITE  )
    multi.text_cancel = helper.Text("M to cancel", font6,Vector2(1, 1), WHITE  )
    multi.text_start = helper.Text(" Press\n    A\nto start", font16,Vector2(1, 1), WHITE  )
    multi.text_countdown = helper.Text("Ready",font16,Vector2(2, 2), WHITE )
    multi.countdown = 2
    
    #init state
    multi.state = GameState(None)
    multi.state.speed = settings.speed
        
    # only for 1 player on a thumby allow  bigger screen
    if localcount == 1:
        size = settings.arena
    else:
        size = 1
    multi.state.width = VIRTUAL_WIDTH[size-1]
    multi.state.height = VIRTUAL_HEIGHT[size-1]
   
    #init controls    
    if multi.local_count == 1:
        multi.state.control.append(control1)
        multi.state.control.append(control1)
    elif multi.local_count == 2:    
        multi.state.control.append(control2)
        multi.state.control.append(control3)
        multi.state.control.append(control2)
        multi.state.control.append(control3)
    elif multi.local_count == 3:    
        multi.state.control.append(control4)
        multi.state.control.append(control5)
        multi.state.control.append(control6)
        multi.state.control.append(control4)
        multi.state.control.append(control5)
        multi.state.control.append(control6)

    #set boost
    if (multi.count > 1) and (multi.count<5):
        if settings.boost == 2:
            multi.state.hasboost = True
            multi.state.boost = 0 # start with 0 collected dots
        elif settings.boost == 1:
            multi.state.hasboost = True
            multi.state.boost = -BOOST_COOLDOWN  # start with charging
            engine_io.indicator(engine_draw.blue)
        else:    
            multi.state.hasboost = False
    else:
        multi.state.hasboost = False
        
    #set bonus
    if multi.device_count == 1:
        multi.state.hasbonus = settings.bonus == 1
            

    multi.register("speed", multiplayer.VALUE_BYTE)
    multi.register("x", multiplayer.VALUE_WORD, True)
    multi.register("y", multiplayer.VALUE_WORD, True)
    multi.register("d", multiplayer.VALUE_BYTE, True)
    multi.register("t", multiplayer.VALUE_BYTE, True)
    multi.register("c", multiplayer.VALUE_BYTE, True)    
    multi.register("b", multiplayer.VALUE_BYTE, True)    
    multi.register("p", multiplayer.VALUE_WORD, True)    

    multi.cb_init_game = cbinitgame
    multi.cb_init_player = cbinitplayer
    multi.cb_identify_players = cbidentifyplayers
    
    log.info("before start "+multi.debug())
    if multi.start():
        log.info("after start "+multi.debug())
        multi.cb_player = cbplayer
        #multi.cb_work = cbwork
        multi.cb_display = cbdisplay
        
        fpsnode = addFPS()
        
        virtual_screen, arena = initScreen(VIRTUAL_WIDTH[size-1], VIRTUAL_HEIGHT[size-1])
        multi.state.arena = arena
        multi.state.screen = virtual_screen
        
        
        log.info("loop "+multi.debug())
        while multi.running():
            if engine.tick():
                updateFPS(fpsnode)

        multi.cb_host = None
        multi.cb_work = None

        finishScreen(multi.state.arena)
        won = multi.state.won
        if won >= 0:
            points = multi.read_player("p", won)
        else:
            points = 0 #multi.read_player("p", 0)
        #if multi.state.won:
        #    points += POINTS_WON 
            
        if settings.showfps:
            fpsnode.mark_destroy()
    else:
        points = 0
        won = -1;

    #remove any messages that might be left
    engine_link.clear_send()
    engine_link.clear_read()

    #multi.stop()    
    multi.mark_destroy()
    engine_io.rumble(0)

    return won, points


def displayTitle():
    engine.fps_limit(60)

    logo_node = Sprite2DNode(
        position=Vector2(0, 80),
        texture=logo,
        opacity=0.0,
    )

    text1 = Text2DNode(
        position=Vector2(-50, 16),
        text="A\nB\nU\nM",
        font=font16,
        line_spacing=1,
        color=WHITE,
        scale=Vector2(1, 1),
        opacity=0.0,
    )
    text2 = Text2DNode(
        position=Vector2(10, 16),
        text="Start\nOptions\nHighscore\nQuit",
        font=font16,
        line_spacing=1,
        color=WHITE,
        scale=Vector2(1, 1),
        opacity=0.0,
    )

    page = 0
    count = 0

    ypos = 80
    opacity = 0

    while True:
        if engine.tick():
            logo_node.position = Vector2(0, ypos)
            logo_node.opacity = opacity
            if ypos > -40:
                ypos -= 1
            else:
                text1.opacity = 1
                text2.opacity = 1

            if opacity < 1:
                opacity = opacity + 0.002

            count += 1

            # check buttons
            if engine_io.A.is_just_pressed:
                page = PAGE_GAME
                break
            if engine_io.B.is_just_pressed:
                page = PAGE_OPTIONS
                break
            if engine_io.MENU.is_just_pressed:
                page = PAGE_QUIT
                break
            if engine_io.UP.is_just_pressed:
                if settings.highscore_id() != "":
                    page = PAGE_HIGHSCORE
                    break
            if engine_io.DOWN.is_just_pressed:
                    page = PAGE_TEST
                    break
    logo_node.mark_destroy()
    text1.mark_destroy()
    text2.mark_destroy()
    return page


def displayPoints(points, won = -1):
    global settings

    #if settings.link:
    #    if won:
    #        text = "Victory!"
    #    else:
    #        text = "Lost!"
    #else:
    #    text = "Crash!"
    text = "Player "+str(won+1)
    if won >= 0:
        c = PLAYER_COLOR[1][won]
    else:
        c = WHITE

    crash = Text2DNode(
        position=Vector2(0, -30),
        text=text,
        font=font16,
        color=c,
        scale=Vector2(2, 2),
    )

    pointst = Text2DNode(
        position=Vector2(0, 0),
        text="Points",
        font=font16,
        color=WHITE,
        scale=Vector2(1, 1),
    )

    points = Text2DNode(
        position=Vector2(0, 20),
        text=str(points),
        font=font16,
        color=WHITE,
        scale=Vector2(2, 2),
    )

    while True:
        if engine.tick():
            if engine_io.A.is_just_pressed:
                break
            if engine_io.B.is_just_pressed:
                break
    crash.mark_destroy()
    pointst.mark_destroy()
    points.mark_destroy()


def test():
    nodes = []
    for x in range(0,3):
        for y in range(0,6):
            c = PLAYER_COLOR[x][y]
            position = Vector2(x*21-64+10,y*21-64+10)
            node = Rectangle2DNode(position,20,20, c)
            nodes.append(node)
    
    while True:
        if engine.tick():
            if engine_io.A.is_just_pressed:
                break
    for node in nodes:
        node.mark_destroy()
            
    

def displayHighscore():
    score.show(settings.highscore_id())
   
def displayOptions():
    global options
    
    title = helper.Text("Options",font16,Vector2(1.5, 1.5),WHITE)
    help = helper.Text("U/D Select\nL/R Change\nA Ok B Help",font6,Vector2(1, 1),YELLOW)
    info = helper.Text(VERSION,font6,Vector2(1, 1), YELLOW)
    listformat = options.OptionsFormat(font16, Vector2(1, 1),WHITE, GREEN, 84)

    data=settings.get()
    node =  options.OptionsNode(title, help, info, listformat, BLACK, data)
    node.load("wallracer.options")
    
    node.show()
    
    settings.set(data)
    settings.save()


    node.mark_destroy()


def addexplosion(x, y, state):
    for count in range(EXPLOSION_BITS):
        # x,y x speed, y speed
        bit = [
            x,
            y,
            (random.randint(0, 20) - 10) / 20,
            (random.randint(0, 20) - 10) / 20,
        ]
        state.bits.append(bit)
    fixexplosion(state)            
    engine_io.rumble(EXPLOSION_RUMBLE)
    state.explosion = EXPLOSION_STEPS * 2   

def clearexplosion(state):
    for bit in state.bits:
        state.screen.pixel(int(bit[0]), int(bit[1]), BACKGROUND)
    state.bits = []    

def fixexplosion(state):
    for bit in state.bits:
        if bit[0] < 1:
            bit[0] = 1
        if bit[0] >= state.width - 1:
            bit[0] = state.width - 2

        if bit[1] < 1:
            bit[1] = 1
        if bit[1] >= state.height - 1:
            bit[1] = state.height - 2


def moveexplosion(state):
    # remove from current position
    for bit in state.bits:
        state.screen.pixel(int(bit[0]), int(bit[1]), BACKGROUND)
        
    # move bits to new position
    for bit in state.bits:
        bit[0] = bit[0] + bit[2]
        bit[1] = bit[1] + bit[3]
    fixexplosion(state)    

    # draw at new position
    for bit in state.bits:
        state.screen.pixel(int(bit[0]), int(bit[1]), EXPLOSION)


page = 1
while page != PAGE_QUIT:
    if page == PAGE_TITLE:
        page = displayTitle()
    if page == PAGE_GAME:
        won, points = playGame()
        if won >=0:
          displayPoints(points, won)
        if settings.highscore_id() != "":
            score.check(settings.highscore_id(), points)
        page = PAGE_TITLE
    if page == PAGE_OPTIONS:
        displayOptions()
        page = PAGE_TITLE
    if page == PAGE_WAITFORPLAYER:
        page = waitForPlayer()
    if page == PAGE_HIGHSCORE:
        displayHighscore()
        page = PAGE_TITLE        
    if page == PAGE_ENTERHIGHSCORE:
        enterHighscore(points)
        page = PAGE_HIGHSCORE
    if page == PAGE_TEST:
        test()
        page = PAGE_TITLE


engine.tick()

