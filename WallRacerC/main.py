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
VERSION = "V1.41"
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

# message kind
KIND_RUNNING =  1
KIND_CRASH1 =  2
KIND_CRASH2 =  3

KIND_SETTINGS = 1
KIND_COUNTDOWN = 2
KIND_PLAYER = 3
KIND_EXPLOSION = 4

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
PLAYER1 = GREEN
PLAYER1A = 0x0c64  # darkgreen
PLAYER1B = 0x4eec  # medium green
PLAYER1C = 0x7ff2  # light green
PLAYER2 = BLUE
PLAYER2A = 0x0291  # dark blue
PLAYER2B = 0x4479  # medium blue
PLAYER2C = 0x65bf  # light blue

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
    game_mode = engine_save.load("gamemode", 0)
    speed = engine_save.load("speed", 5) 
    
def saveSettings():
    global game_mode
    global speed
    engine_save.set_location("wallracer.data")
    engine_save.save("gamemode", game_mode)
    engine_save.save("speed", speed) 


# Global Vars
speed = 5  # speed of the game
boost = 0
bonus = []  # position of bonus dots
game_mode = MODE_LINK  # 0 = full with bonus dots 1 = pure 2 = multiplayer
player_x = 0
player_y = 0
player_direction = 0
lasthigh = "AAA"
showfps = False

loadSettings()
score = initHighscore()

# for multiplayer
first_player = True


# Add a bonus dot at random position but keep distance to other dots and player
def addBonus():
    global player_x
    global player_y

    ok = False

    while not ok:
        ok = True
        x = random.randint(BONUS_BORDER_DISTANCE, VIRTUAL_WIDTH - BONUS_BORDER_DISTANCE)
        y = random.randint(BONUS_BORDER_DISTANCE, VIRTUAL_HEIGHT - BONUS_BORDER_DISTANCE)

        # check distance to player
        if (
            (x >= player_x - BONUS_DISTANCE)
            and (x <= player_x + BONUS_DISTANCE)
            and (y >= player_y - BONUS_DISTANCE)
            and (y <= player_y + BONUS_DISTANCE)
        ):
            ok = False

        # check distance to other bonus
        for point in bonus:
            if (
                (x >= point[0] - BONUS_DISTANCE)
                and (x <= point[0] + BONUS_DISTANCE)
                and (y >= point[1] - BONUS_DISTANCE)
                and (y <= point[1] + BONUS_DISTANCE)
            ):
                ok = False

    point = [x, y]
    bonus.append(point)


# Add inital bonus
def initBonus():
    bonus.clear()
    for c in range(BONUS_COUNT):
        addBonus()


# Draw one bonus dot at x,y location
def drawBonus(x, y, animation):
    if animation == -1:
        color = BACKGROUND
    else:
        color = ANIMATION[int(animation // 5) % 2]

    # draw 3x3 dot
    for nx in range(x - 1, x + 2):
        virtual_screen.vline(nx, y - 1, 3, color)


# Draw all bonus dots from the list
def drawBonusList(animation):
    for point in bonus:
        drawBonus(point[0], point[1], animation)


# Check if a bonus is at location x,y if yes remove it from screen and return the index in the list
def checkBonus(x, y):
    hit = -1
    for index in range(len(bonus)):
        point = bonus[index]
        if (
            (x >= point[0] - BONUS_TOLERANCE)
            and (x <= point[0] + BONUS_TOLERANCE)
            and (y >= point[1] - BONUS_TOLERANCE)
            and (y <= point[1] + BONUS_TOLERANCE)
        ):
            # remove the bonus
            drawBonus(point[0], point[1], -1)
            hit = index
    return hit


#move arena sprite so the player is in the middle of the screen
def updateScreen(arena):
    global player_x
    global player_y

    # update screen
    screen_x = SCREEN_WIDTH - player_x
    screen_y = SCREEN_HEIGHT -  player_y

    arena.position = Vector2(screen_x,screen_y)

#wait for next frame and display it
def refreshScreen():
    sleep_time = engine.time_to_next_tick() / 1000
    time.sleep(sleep_time)
    engine.tick()

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

#display the bonus for a short time
def displayBonus(points):
    text_bonus = Text2DNode(
        position=Vector2(0, -20),
        text="Bonus!",
        font=font16,
        line_spacing=1,
        color=WHITE,
        scale=Vector2(2, 2),
    )

    text_points = Text2DNode(
        position=Vector2(0, 20),
        text=str(points),
        font=font16,
        line_spacing=1,
        color=WHITE,
        scale=Vector2(2, 2),
    )

    refreshScreen()
    time.sleep(1)
    text_bonus.mark_destroy()
    text_points.mark_destroy()


def playerColor():
    global game_mode
    global first_player
    global boost
    
    if game_mode == MODE_LINK:
        if first_player:
            if boost < 0:
                color = PLAYER1A
            elif boost == 0:
                color = PLAYER1B
            else:
                color = PLAYER1C
        else:
            if boost < 0:
                color = PLAYER2A
            elif boost == 0:
                color = PLAYER2B
            else:
                color = PLAYER2C
    else:
        if first_player:
            color = PLAYER1
        else:
            color = PLAYER2
    return color

class GameState():
    def __init__(self, screen):
        self.points = 0
        self.won = True
        self.screen = screen
        # for explosions
        self.bits = []
        self.explosion = 0

        
def handlePlayer(multi,index):
    global virtual_screen

    x = multi.read("x",index)
    y = multi.read("y",index)
    direction = multi.read("d",index)
    throttle = multi.read("t",index)
    crash1 = multi.read("c",0)
    if multi.player_count == 2:
        crash2 = multi.read("c",1)
    else:
        crash2 = 0
     
    # if no player has crashed move
    if (crash1 == 0) and (crash2 == 0):
        if engine_io.LB.is_just_pressed:
            direction = (direction - 1) % 4
            multi.write("d", direction,index)

        # Turn right on RB
        if engine_io.RB.is_just_pressed:
            direction = (direction + 1) % 4
            multi.write("d", direction,index)
        
        if multi.counter % throttle == 0:
            x += PLAYERXADD[direction]
            y += PLAYERYADD[direction]
            multi.write("x", x,index)
            multi.write("y", y,index)
            
            multi.state.points += 1


            if virtual_screen.pixel(x, y) != BACKGROUND:
                multi.write("c", 1,index)
                multi.state.won = False

def cbclient(multi):
    handlePlayer(multi, 1)

def cbhost(multi):
    handlePlayer(multi, 0)

arena = None

def cbwork(multi):
    global arena
    global virtual_screen

    if multi.is_host():
        this = 0
    else:
        this = 1

    #draw player
    for player in range(0,multi.player_count):
        x = multi.read("x", player)
        y = multi.read("y", player)
        c = multi.read("c", player)
        if c == 0:
            multi.state.screen.pixel(x, y, PLAYER_COLOR[player])
        elif c == 1:
            addexplosion(x,y, multi.state)
            multi.write("c",2,player)
        #center on this player            
        if player == this:
            screenx = SCREEN_WIDTH - x
            screeny = SCREEN_HEIGHT - y
            arena.position = Vector2(screenx, screeny)

    if multi.state.explosion > 0:
        moveexplosion(multi.state)
        multi.state.explosion -= 1

        #when explosion finshed stop ther game
        if multi.state.explosion == 0:
            time.sleep(0.5)        
            multi.cancel()

def cbinit(multi):
    global speed
    print("cbinit "+str(multi.player_count))
    throttle = 11 - speed

    for player in range (0,multi.player_count):
        if multi.player_count == 1:
            startpos = random.randint(0, 3)
        else:
            startpos = random.randint(player*2, player*2+1)
        print("startpos "+str(startpos))    
        start = START_POSITIONS[startpos]
        multi.write("x", start[0], player)
        multi.write("y", start[1], player)
        multi.write("d", start[2], player)
        multi.write("t", throttle, player)
        multi.write("c", 0, player)
        print(multi.debug())
         


def initScreen():
    global virtual_screen
    global arena
    log.info("initScreen")
    
    # Clear virtual screen
    virtual_screen.fill(BACKGROUND)
    # Add the frame
    drawFrame(virtual_screen)
    arena = Sprite2DNode(texture=texture)
    log.info("initScreen done")
    
def finishScreen():    
    global arena
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
    
    engine.fps_limit(120)


    multi = multiplayer.MultiplayerNode()
    multi.state = GameState(virtual_screen)
        
    multi.register("x", multiplayer.VALUE_WORD)
    multi.register("y", multiplayer.VALUE_WORD)
    multi.register("d", multiplayer.VALUE_BYTE)
    multi.register("t", multiplayer.VALUE_BYTE)
    multi.register("c", multiplayer.VALUE_BYTE)    

    multi.cb_init = cbinit
    
    if multi.start(False):
        log.info("start ok")
        initScreen()
        multi.cb_host = cbhost
        multi.cb_work = cbwork

        fpsnode = addFPS()

        while multi.running():
            if engine.tick():
                updateFPS(fpsnode)
        print_memory_usage()
        finishScreen()
        points = multi.state.points
        if showfps:
            fpsnode.mark_destroy()


    multi.mark_destroy()
        
    return points
            


def playMultiplayerGame():
    global showfps
    global virtual_screen
    
    engine.fps_limit(120)
    
    multi = multiplayer.MultiplayerNode()
    multi.state = GameState(virtual_screen)
    
    multi.countdown = 2
    
    bits = []

    multi.text_connecting = helper.Text("Connecting", font16,Vector2(1, 1), WHITE  )
    multi.text_cancel = helper.Text("M to cancel", font6,Vector2(1, 1), WHITE  )
    multi.text_start = helper.Text("    Press\n       A\nwhen ready", font16,Vector2(1, 1), WHITE  )
    multi.text_countdown = helper.Text("Ready",font16,Vector2(2, 2), WHITE )
    
    # d = direction
    # t = throttel
    # c = crash
    # e = explosion counter
    multi.register("x", multiplayer.VALUE_WORD,2)
    multi.register("y", multiplayer.VALUE_WORD,2)
    multi.register("d", multiplayer.VALUE_BYTE,2)
    multi.register("t", multiplayer.VALUE_BYTE,2)
    multi.register("c", multiplayer.VALUE_BYTE,2)    


    multi.cb_init = cbinit

    log.info("before start")
    
    if multi.start():
        log.info("start ok")
        initScreen()
        multi.cb_client = cbclient
        multi.cb_host = cbhost
        multi.cb_work = cbwork
        
        fpsnode = addFPS()
        
        log.info("loop")
        while multi.running():
            if engine.tick():
                updateFPS(fpsnode)

        finishScreen()
        points = multi.state.points
        if multi.state.won:
            points += POINTS_WON 
        won = multi.state.won
            
        if showfps:
            fpsnode.mark_destroy()
    else:
        points = 0
        won = False;
        
    multi.mark_destroy()

    return won, points


def playGame():
    global texture
    global game_mode
    global speed
    global player_x
    global player_y
    global player_direction
    global virtual_screen
    global first_player
    global won
    global boost
    global showfps

    log("Game")

    engine.fps_limit(120)
    #engine.disable_fps_limit()

    first_player = True
    ok = True
    if game_mode == MODE_LINK:
        multi = multiplayer.MultiplayerNode()

        multi.text_connecting = helper.Text("Connecting", font16,Vector2(1, 1), WHITE  )
        multi.text_cancel = helper.Text("M to cancel", font6,Vector2(1, 1), WHITE  )
        multi.text_start = helper.Text("    Press\n       A\nwhen ready", font16,Vector2(1, 1), WHITE  )
        multi.text_countdown = helper.Text("Ready",font16,Vector2(2, 2), WHITE )
        
        multi.register("kind", multiplayer.VALUE_BYTE)
        multi.register("x1", multiplayer.VALUE_WORD)
        multi.register("y1", multiplayer.VALUE_WORD)
        multi.register("x2", multiplayer.VALUE_WORD)
        multi.register("y2", multiplayer.VALUE_WORD)

        multi.cb_client = cbclient
        multi.cb_host = cbhost
        multi.cb_work = cbwork

        ok = multi.start()
        first_player = multi.is_host()
        
    if ok:
        if showfps:
            fpsnode =  Text2DNode(
              position=Vector2(0, 0),
              text="FPS",
              font=font16,
              line_spacing=1,
              color=YELLOW,
              scale=Vector2(1, 1),
              layer=100
            )
            helper.align_top(fpsnode)
            helper.align_left(fpsnode)

        initScreen()


        # start with cooldown
        boost = -BOOST_COOLDOWN

        # Initialize player position in one of the corners
        setStartPosition()

        # points player has collected for this game
        points = 0
        # used for bonus flashing and speed
        counter = 0

        # Bonus dots only for full game
        if game_mode == MODE_FULL:
            initBonus()

        # refresh speed
        throttle = 11 - speed

        #add a sprite displaying the virtual_screen
        arena = Sprite2DNode(texture=texture)
        updateScreen(arena)
        won = True

        log("Loop")
        fpscount = FPSAVERAGECOUNT
        fpssum = 0
        while won:
            if engine.tick():
                if showfps:
                    fps = engine.get_running_fps()
                    fpssum += fps
                    fpscount -= 1
                    if fpscount == 0:
                        fpsnode.text = str(fpssum // FPSAVERAGECOUNT)
                        helper.align_left(fpsnode)
                        fpssum = 0
                        fpscount = FPSAVERAGECOUNT

                # Turn left on LB
                if engine_io.LB.is_just_pressed:
                    player_direction = (player_direction - 1) % 4

                # Turn right on RB
                if engine_io.RB.is_just_pressed:
                    player_direction = (player_direction + 1) % 4

                # Start boost on B
                if (game_mode == MODE_LINK) and (boost == 0) and engine_io.B.is_just_pressed:
                    boost = BOOST_TIME
                    throttle -= BOOST_SPEED
                    engine_io.rumble(BOOST_RUMBLE)
                    #limit throttle to max speed
                    if throttle < 1:
                        throttle = 1

                # throttle player
                if counter % throttle == 0:
                    # update boost
                    if game_mode == MODE_LINK:
                        if boost < 0:
                            boost += 1
                        elif boost > 0:
                            boost -= 1
                            if boost == 0:
                                # return to normal speed
                                throttle = 11 - speed
                                engine_io.rumble(0)
                                # start cooldown
                                boost = -BOOST_COOLDOWN
                    # calculate new player position
                    player_x += PLAYERXADD[player_direction]
                    player_y += PLAYERYADD[player_direction]

                    # check for bonus
                    if game_mode == MODE_FULL:
                        hit = checkBonus(player_x, player_y)
                        if hit >= 0:
                            # if hit remove the existing bonus and add a new one
                            del bonus[hit]
                            addBonus()
                            bonus_points = speed * BONUS_FACTOR
                            log("Bonus: " + str(bonus_points))
                            points += bonus_points
                            displayBonus(bonus_points)

                    # check for crash
                    if virtual_screen.pixel(player_x, player_y) != BACKGROUND:
                        # always in the middle of the screen
                        explosion(player_x, player_y, arena)
       
                        if game_mode == MODE_LINK:
                            won = False 
                            # send explosion
                            #multi.write("kind", KIND_EXPLOSION)
                            #if first_player:
                            #  multi.write("x", player_x)
                            #  multi.write("y", player_y)

                        time.sleep(0.5)
                        

                    # Draw the player
                    color = playerColor()
                    virtual_screen.pixel(player_x, player_y, color)

                    # increase points for survival
                    points += 1

                # flash bonus points
                if game_mode == MODE_FULL:
                    drawBonusList(counter)

                # muliplayer messages
                if game_mode == MODE_LINK:
                    kind = multi.read("kind")
                    x1 = multi.read("x1")
                    y1 = multi.read("y1")
                    x2 = multi.read("x2")
                    y2 = multi.read("y2")

                    if kind == KIND_PLAYER:
                        # player position
                        if first_player:
                            virtual_screen.pixel(x2, y2, PLAYER2)
                        else:
                            virtual_screen.pixel(x1, y1, PLAYER1)
                    elif kind == KIND_EXPLOSION:
                        # explosion of other player
                        if first_player:    
                            explosion(x2, y2, arena)
                        else:    
                            explosion(x1, y1, arena)
                        won = True
                        points += POINTS_WON
                        time.sleep(0.5)
                        break


                    if first_player:    
                        multi.write("x1", player_x)
                        multi.write("y1", player_y)
                    else:    
                        multi.write("x2", player_x)
                        multi.write("y2", player_y)


                    if won:
                        multi.write("kind", KIND_PLAYER)
                    else:
                        multi.write("kind", KIND_EXPLOSION)
                        # make sure the explosion is set, loop will exit
                        engine.tick()
                        
                    

                counter += 1
                updateScreen(arena)
        
        # always stop rumble
        engine_io.rumble(0)

        if showfps:
            fpsnode.mark_destroy()

        #remove the arena sprite
        arena.mark_destroy()

        # clear all remaining messages in usb buffer for next game
        if game_mode == MODE_LINK:
            multi.stop()
            multi.mark_destroy()

    return points


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
    global first_player
    global speed
    global showfps
    
    title = helper.Text("Options",font16,Vector2(1.5, 1.5),WHITE)
    help = helper.Text("U/D Select\nL/R Change\nA Ok B Help",font6,Vector2(1, 1),YELLOW)
    info = helper.Text(VERSION,font6,Vector2(1, 1), YELLOW)
    listformat = options.OptionsFormat(font16, Vector2(1, 1),WHITE, GREEN, 84)

    gamemodes = [options.OptionsValue("Full",MODE_FULL),
                 options.OptionsValue("Pure",MODE_PURE),
                 options.OptionsValue("Link",MODE_LINK),
                ]



    gamespeeds = []
    for sp in range(1,11):
        gamespeeds.append(options.OptionsValue(str(sp),sp))

    data={}
    node =  options.OptionsNode(title, help, info, listformat, BLACK, data)
    helptext=("Dont crash in any Wall. Use left and right shoulder buttons to stear.\n\n"
              "Full\n"
              "Collect flashing dots for bonus points.\n\n"
              "Pure\n"
              "Just you and the line.\n\n"
              "Link\n"
              "Multiplayer using a link cable. Use B for temporary speed boost. Line color shows if ready to boost."
             )
    
    helptext = helper.word_wrap(helptext, font16, Vector2(1,1), SCREEN_WIDTH)
    node.addoption("Mode:", helptext,"mode", gamemodes, game_mode)

    helptext=("Speed of the game, 10 is fastest.\n"
              "There is a highscore for each speed.\n"
              "Boost in link mode is speed + 3 so use a maximum of 7 for link mode."
             )
    
    helptext = helper.word_wrap(helptext, font16, Vector2(1,1), SCREEN_WIDTH)

    node.addoption("Speed:",helptext ,"speed", gamespeeds, speed)
    
    offon = [options.OptionsValue("Off", False),
             options.OptionsValue("On", True)
            ]

    node.addoption("ShowFPS:", "", "showfps", offon, showfps)
    
    node.show()
    
    game_mode = data["mode"]
    speed = data["speed"]
    showfps = data["showfps"]

    print("mode="+str(game_mode))
    print("speed="+str(speed))

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
log("Exit")
