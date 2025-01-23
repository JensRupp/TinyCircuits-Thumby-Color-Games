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
VIRTUAL_WIDTH = SCREEN_WIDTH * 2 
VIRTUAL_HEIGHT = SCREEN_HEIGHT * 2 
BYTES_PER_PIXEL = 2
BYTE_SIZE = VIRTUAL_WIDTH * VIRTUAL_HEIGHT * BYTES_PER_PIXEL
BONUS_FACTOR = 20  # points for collecting a bonus dot multiplied by speed
BONUS_DISTANCE = 20  # minimum distance between dots
BONUS_COUNT = 3  # number of bonus dots displayed
BONUS_TOLERANCE = 1  # how near the player needs to be to collect the bonus
BONUS_BORDER_DISTANCE = 10 # minimum distance from border for bonus points 
EXPLOSION_BITS = 72  # number of pixels in the explosion
EXPLOSION_STEPS = 20  # number of steps the explosion runs
EXPLOSION_RUMBLE = 0.4 # rumble intensity during explosion
POINTS_WON = 1000  # extra points for winning
BOOST_COOLDOWN = 80  # number of pixels to wait for next boost
BOOST_TIME = 40  # number of pixels to boost
BOOST_SPEED = 3  # increase of speed during boost
BOOST_RUMBLE = 0.2  # rumble intensity during boost
# map direction to offsets
PLAYERXADD = [1, 0, -1, 0]  # mapping of direction to x add
PLAYERYADD = [0, 1, 0, -1]  # mapping of direction to y add
START_POSITIONS = [
    [30, 30, 0],
    [30, VIRTUAL_HEIGHT - 30, 0],
    [VIRTUAL_WIDTH - 30, 30, 2],
    [VIRTUAL_WIDTH - 30, VIRTUAL_HEIGHT - 30, 2],
]
FPSAVERAGECOUNT = 10

# game modes
MODE_FULL = 0
MODE_PURE = 1
MODE_LINK = 2

# pages
PAGE_QUIT = 0
PAGE_TITLE = 1
PAGE_GAME = 2
PAGE_OPTIONS = 3
PAGE_WAITFORPLAYER = 4
PAGE_HIGHSCORE = 5
PAGE_ENTERHIGHSCORE = 6

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
PLAYER_COLOR=[GREEN, BLUE]
EXPLOSION = RED
ANIMATION = [YELLOW, RED]


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

# Virtual Screen and graphics
texture = TextureResource(VIRTUAL_WIDTH, VIRTUAL_HEIGHT,0,16)
virtual_screen = framebuf.FrameBuffer(texture.data, texture.width, texture.height, framebuf.RGB565)

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
    for mode in range(0,2):
        if mode == MODE_FULL:
            ext = "Full"
        else:
            ext = "Pure"            
        
        for speed in range(1,11):
            id=str(mode)+'-'+str(speed)
            name = ext +" Speed " + str(speed)
            score.register(id, name, 100, "GAC")
            
    return score 

def loadSettings():
    global game_mode
    global speed
    engine_save.set_location("wallracer.data")
    game_mode = engine_save.load("gamemode", MODE_FULL)
    speed = engine_save.load("speed", 5) 
    
def saveSettings():
    global game_mode
    global speed
    engine_save.set_location("wallracer.data")
    engine_save.save("gamemode", game_mode)
    engine_save.save("speed", speed) 


# Global Vars
speed = 5  # speed of the game
game_mode = MODE_FULL  # 0 = full with bonus dots 1 = pure 2 = multiplayer
showfps = False

loadSettings()
score = initHighscore()

# Add a bonus dot at random position but keep distance to other dots and player
def addBonus(multi):
    ok = False
    while not ok:
        ok = True
        x = random.randint(BONUS_BORDER_DISTANCE, VIRTUAL_WIDTH - BONUS_BORDER_DISTANCE)
        y = random.randint(BONUS_BORDER_DISTANCE, VIRTUAL_HEIGHT - BONUS_BORDER_DISTANCE)

        # check distance to players
        for player in range(0,multi.player_count):
            player_x = multi.readi("x", player)
            player_y = multi.readi("y", player)
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
def drawFrame(screen):
    screen.rect(0, 0, VIRTUAL_WIDTH , VIRTUAL_HEIGHT , FRAME1)

    lw = int(SCREEN_WIDTH / 4)
    c = int((VIRTUAL_WIDTH / (lw * 2)) )
    for step in range(c):
        screen.hline(lw + step * lw * 2, 0, lw, FRAME2)
        screen.hline(lw + step * lw * 2, VIRTUAL_HEIGHT - 1, lw, FRAME2)

    w = int(SCREEN_HEIGHT / 4)
    c = int((VIRTUAL_HEIGHT / (lw * 2)) )
    for step in range(c):
        screen.vline(0, lw + step * lw * 2, lw, FRAME2)
        screen.vline(VIRTUAL_WIDTH - 1, lw + step * lw * 2, lw, FRAME2)

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
    #display for one second
    state.sleep =  engine.fps_limit()


class GameState():
    def __init__(self, screen):
        self.points = 0
        self.won = True
        self.screen = screen
        self.arena = None
        # for explosions
        self.bits = []
        self.explosion = 0
        # for bonus points
        self.hasbonus = False
        self.bonus = []
        
        self.throttle = 0
        
        # for bonus point display
        self.sleep = 0
        self.bonus1 = None
        self.bonus2 = None

        self.hasboost = False
        self.boost = 0
        

        
def handlePlayer(multi,index):
    
    if multi.state.sleep > 0:
        multi.state.sleep -= 1
        
        if multi.state.sleep < 1 :
            multi.state.sleep = 0 # fix strange rounding error
            multi.state.bonus1.mark_destroy()
            multi.state.bonus2.mark_destroy()
    else:
        x = multi.readi("x",index)
        y = multi.readi("y",index)
        direction = multi.readi("d",index)
        
        crash1 = multi.readi("c",0)
        if multi.player_count == 2:
            crash2 = multi.readi("c",1)
        else:
            crash2 = 0
         
        # if no player has crashed move
        if (crash1 == 0) and (crash2 == 0):
            if engine_io.LB.is_just_pressed:
                direction = (direction - 1) % 4
                multi.writei("d", direction,index)

            # Turn right on RB
            if engine_io.RB.is_just_pressed:
                direction = (direction + 1) % 4
                multi.writei("d", direction,index)
                
            # Start boost on B
            if multi.state.hasboost and (multi.state.boost == 0) and engine_io.B.is_just_pressed:
                multi.state.boost = BOOST_TIME
                multi.state.throttle -= BOOST_SPEED
                #limit throttle to max speed
                if multi.state.throttle < 1:
                    multi.state.throttle = 1
                engine_io.indicator(engine_draw.red)    
                
                
            
            if multi.counter % multi.state.throttle == 0:
                
                if multi.state.hasboost:
                    if multi.state.boost < 0:
                        multi.state.boost += 1
                        if multi.state.boost == 0:
                            engine_io.indicator(engine_draw.green)
                    elif multi.state.boost >  0:
                        multi.state.boost -= 1
                        if multi.state.boost == 0:
                            speed = multi.read("speed")
                            throttle = 11 - speed
                            boost = -BOOST_COOLDOWN
                            engine_io.indicator(engine_draw.blue)
                
                
                x += PLAYERXADD[direction]
                y += PLAYERYADD[direction]
                multi.writei("x", x,index)
                multi.writei("y", y,index)
                
                multi.state.points += 1

                if multi.state.hasbonus: 
                    hit = checkBonus(x, y, multi.state)
                    if hit >= 0:
                        # if hit remove the existing bonus and add a new one
                        del multi.state.bonus[hit]
                        addBonus(multi)
                        speed = multi.read("speed")
                        bonus_points = speed * BONUS_FACTOR
                        multi.state.points += bonus_points
                        displayBonus(bonus_points, multi.state)


                if multi.state.screen.pixel(x, y) != BACKGROUND:
                    multi.writei("c", 1,index)
                    multi.state.won = False

# speed calculation:
# host writes speed on init to "speed"
# client checks if hios values is smaller, if yes write to "speed"
# client uses the sameller value to init throttle
# host reads trhe possibly upüdates "speed" and uses that to init throttle
def cbclient(multi):
    global speed
    #init speed on minimum of host and client
    if multi.state.throttle == 0:
        hostspeed = multi.read("speed")
        if speed < hostspeed:
            hostspeed = speed
            multi.write("speed",hostspeed)
        multi.state.throttle = 11 - hostspeed
    
    handlePlayer(multi, 1)

def cbhost(multi):
    #init speed on minimum of host and client
    if multi.state.throttle == 0:
        hostspeed = multi.read("speed")
        multi.state.throttle = 11 - hostspeed

    handlePlayer(multi, 0)

def cbwork(multi):
    if multi.is_host():
        this = 0
    else:
        this = 1

    #draw player
    for player in range(0,multi.player_count):
        x = multi.readi("x", player)
        y = multi.readi("y", player)
        c = multi.readi("c", player)
        if c == 0:
            multi.state.screen.pixel(x, y, PLAYER_COLOR[player])
        elif c == 1:
            addexplosion(x,y, multi.state)
            multi.writei("c",2,player)
        #center on this player            
        if player == this:
            screenx = SCREEN_WIDTH - x
            screeny = SCREEN_HEIGHT - y
            multi.state.arena.position = Vector2(screenx, screeny)

    if multi.state.hasbonus:
        drawBonusList(multi.counter, multi.state)


    if multi.state.explosion > 0:
        moveexplosion(multi.state)
        multi.state.explosion -= 1

        #when explosion finshed stop ther game
        if multi.state.explosion == 0:
            engine_io.rumble(0)
            time.sleep(0.5)        
            multi.cancel()

# initialize the synced data on the host
def cbinit(multi):
    global speed

    multi.write("speed", speed)

    for player in range (0,multi.player_count):
        if multi.player_count == 1:
            startpos = random.randint(0, 3)
        else:
            startpos = random.randint(player*2, player*2+1)
       
        start = START_POSITIONS[startpos]
        multi.writei("x", start[0], player)
        multi.writei("y", start[1], player)
        multi.writei("d", start[2], player)
        multi.writei("c", 0, player)
        
    if multi.state.hasbonus:       
        initBonus(multi)



def initScreen():
    global virtual_screen
    
    # Clear virtual screen
    virtual_screen.fill(BACKGROUND)
    # Add the frame
    drawFrame(virtual_screen)
    arena = Sprite2DNode(texture=texture)
    return arena
    
def finishScreen(arena):    
    arena.mark_destroy()

fpscount = FPSAVERAGECOUNT
fpssum = 0

def addFPS():
    global showfps
    node = None
    if showfps:
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
    global showfps
    
    if showfps:
        fps = engine.get_running_fps()
        fpssum += fps
        fpscount -= 1
        if fpscount == 0:
            fpsnode.text = str(int(fpssum // FPSAVERAGECOUNT))
            #helper.align_left(fpsnode)
            fpssum = 0
            fpscount = FPSAVERAGECOUNT
    

    
def playSingleplayerGame():
    global showfps
    global virtual_screen
    global game_mode
    
    engine.fps_limit(120)


    multi = multiplayer.MultiplayerNode()
    multi.state = GameState(virtual_screen)
    
    # Bonus dots only for full game
    if game_mode == MODE_FULL:
        multi.state.hasbonus = True
    

    multi.register("speed", multiplayer.VALUE_BYTE)
    multi.register("x", multiplayer.VALUE_WORD)
    multi.register("y", multiplayer.VALUE_WORD)
    multi.register("d", multiplayer.VALUE_BYTE)
    multi.register("c", multiplayer.VALUE_BYTE)
    

    multi.cb_init = cbinit
    
    if multi.start(False):
        log.info("start ok")
        multi.state.arena = initScreen()
        multi.cb_host = cbhost
        multi.cb_work = cbwork

        fpsnode = addFPS()

        while multi.running():
            if engine.tick():
                updateFPS(fpsnode)

        finishScreen(multi.state.arena)
        points = multi.state.points
        if showfps:
            fpsnode.mark_destroy()


    multi.mark_destroy()
    engine_io.rumble(0)
    

        
    return points
            


def playMultiplayerGame():
    global showfps
    global virtual_screen
    
    engine.fps_limit(120)
    
    multi = multiplayer.MultiplayerNode()
    multi.state = GameState(virtual_screen)
    multi.state.hasboost = True
    
    if multi.state.hasboost:
        multi.state.boost = -BOOST_COOLDOWN
        engine_io.indicator(engine_draw.blue)
    
    multi.countdown = 2
    
    bits = []

    multi.text_connecting = helper.Text("Connecting", font16,Vector2(1, 1), WHITE  )
    multi.text_cancel = helper.Text("M to cancel", font6,Vector2(1, 1), WHITE  )
    multi.text_start = helper.Text("    Press\n       A\nwhen ready", font16,Vector2(1, 1), WHITE  )
    multi.text_countdown = helper.Text("Ready",font16,Vector2(2, 2), WHITE )
    
    # d = direction
    # c = crash
    multi.register("speed", multiplayer.VALUE_BYTE)
    multi.register("x", multiplayer.VALUE_WORD,2)
    multi.register("y", multiplayer.VALUE_WORD,2)
    multi.register("d", multiplayer.VALUE_BYTE,2)
    multi.register("c", multiplayer.VALUE_BYTE,2)    


    multi.cb_init = cbinit

    log.info("before start")
    
    if multi.start():
        log.info("start ok")
        multi.state.arena = initScreen()
        multi.cb_client = cbclient
        multi.cb_host = cbhost
        multi.cb_work = cbwork
        
        fpsnode = addFPS()
        
        log.info("loop")
        while multi.running():
            if engine.tick():
                updateFPS(fpsnode)

        finishScreen(multi.state.arena)
        points = multi.state.points
        if multi.state.won:
            points += POINTS_WON 
        won = multi.state.won
            
        if showfps:
            fpsnode.mark_destroy()
    else:
        points = 0
        won = False;

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
                page = PAGE_HIGHSCORE
                break
    logo_node.mark_destroy()
    text1.mark_destroy()
    text2.mark_destroy()
    return page


def displayPoints(points, won = True):
    global game_mode

    if game_mode == MODE_LINK:
        if won:
            text = "Victory!"
        else:
            text = "Lost!"
    else:
        text = "Crash!"

    crash = Text2DNode(
        position=Vector2(0, -30),
        text=text,
        font=font16,
        color=WHITE,
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

def modeID():
    global speed
    global game_mode
    
    m = game_mode
    if m == MODE_LINK:
        m = MODE_FULL
    
    return str(m)+"-"+str(speed)

def displayHighscore():
    score.show(modeID())
   
def displayOptions():
    global game_mode
    global speed
    global showfps
    
    title = helper.Text("Options",font16,Vector2(1.5, 1.5),WHITE)
    help = helper.Text("U/D Select\nL/R Change\nA Ok B Help",font6,Vector2(1, 1),YELLOW)
    info = helper.Text(VERSION,font6,Vector2(1, 1), YELLOW)
    listformat = options.OptionsFormat(font16, Vector2(1, 1),WHITE, GREEN, 84)

    data={}
    node =  options.OptionsNode(title, help, info, listformat, BLACK, data)
    node.load("wallracer.options")
    
    node.show()
    
    game_mode = data["mode"]
    speed = data["speed"]
    showfps = data["showfps"]

    saveSettings()

    node.mark_destroy()


def addexplosion(x, y, state):
    for count in range(EXPLOSION_BITS):
        # x,y x speed, y speed
        bit = [
            x,
            y,
            (random.randint(0, 20) - 10) / 10,
            (random.randint(0, 20) - 10) / 10,
        ]
        state.bits.append(bit)
    engine_io.rumble(EXPLOSION_RUMBLE)
    state.explosion = EXPLOSION_STEPS    

def moveexplosion(state):
    # remove from current position
    for bit in state.bits:
        state.screen.pixel(int(bit[0]), int(bit[1]), BACKGROUND)
        
    # move bits to new position
    for bit in state.bits:
        bit[0] = bit[0] + bit[2]
        if bit[0] < 0:
            bit[0] = 0
        if bit[0] >= VIRTUAL_WIDTH:
            bit[0] = VIRTUAL_WIDTH - 1

        bit[1] = bit[1] + bit[3]
        if bit[1] < 0:
            bit[1] = 0
        if bit[1] >= VIRTUAL_HEIGHT:
            bit[1] = VIRTUAL_HEIGHT - 1

    # draw at new position
    for bit in state.bits:
        state.screen.pixel(int(bit[0]), int(bit[1]), EXPLOSION)


page = 1
while page != PAGE_QUIT:
    if page == PAGE_TITLE:
        page = displayTitle()
    if page == PAGE_GAME:
        if game_mode == MODE_LINK:
            won, points = playMultiplayerGame()
            displayPoints(points, won)
        else:
            points = playSingleplayerGame()
            displayPoints(points)
        if (game_mode == MODE_FULL) or (game_mode == MODE_PURE):
            score.check(modeID(), points)
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

engine.tick()

