import os
import engine
from engine_nodes import Rectangle2DNode, CameraNode, Text2DNode, Sprite2DNode
import engine_io
import gc
import engine_draw
import time
import random
from engine_math import Vector2
from engine_resources import FontResource, TextureResource

from settings import Settings
from game import Game, PLAYER_COLOR

from gaclib import options
from gaclib import helper
from gaclib import highscore
from gaclib import multiplayer
from gaclib import logger

# Const Definitions
GAME_NAME = "WallRacer"
VERSION = "V1.7"

VIRTUAL_WIDTH = [int(helper.SCREEN_WIDTH), int(helper.SCREEN_WIDTH * 1.5), int(helper.SCREEN_WIDTH * 2)] 
VIRTUAL_HEIGHT = [int(helper.SCREEN_HEIGHT), int(helper.SCREEN_HEIGHT * 1.5), int(helper.SCREEN_HEIGHT * 2) ]

# pages
PAGE_QUIT = 0
PAGE_TITLE = 1
PAGE_GAME = 2
PAGE_OPTIONS = 3
PAGE_HIGHSCORE = 5
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
    
log = logger.log("/Games/WallRacerC/wallracer.log")
#log.start()
log.info("System Start")

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


# Global Settings
settings = Settings()
settings.load()

score = initHighscore()

def playGame():
    global settings
    
    if settings.link:
        devicecount = 2
        localcount = settings.player2t
    else:
        devicecount = 1
        localcount = settings.player1t
    count = localcount * devicecount    
        
    # only for 1 player on a thumby allow  bigger screen
    if localcount == 1:
        size = settings.arena
    else:
        size = 1

    width = VIRTUAL_WIDTH[size-1]
    height = VIRTUAL_HEIGHT[size-1]
    hasbonusdots = (devicecount == 1) and (settings.bonus == 1)
    hasboost = (count > 1) and (count<5) and (settings.boost == 1)
    
    game = Game(devicecount, localcount, width, height, settings.speed, hasbonusdots, hasboost, settings.showfps, font6, font16, log)
    win, points = game.play()

    
    return count, win, points



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


def displayPoints(count, points, won = -1):
    global settings


    if (won >= 0) and (count>1):
        text = "Player "+str(won+1)
        c = PLAYER_COLOR[1][won]
    else:
        text = "Crash!"
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
    multi = multiplayer.MultiplayerNode(1, 1)
    multi.testbuffer()
    multi.testspeed()
    multi.testspeed2()
    multi.mark_destroy

    
    
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


page = 1
while page != PAGE_QUIT:
    if page == PAGE_TITLE:
        page = displayTitle()
    if page == PAGE_GAME:
        count, won, points = playGame()
        if won >=0:
            displayPoints(count, points, won)
        page = PAGE_TITLE            
        if settings.highscore_id() != "":
            if score.check(settings.highscore_id(), points):
                page = PAGE_HIGHSCORE
    if page == PAGE_OPTIONS:
        displayOptions()
        page = PAGE_TITLE
    if page == PAGE_HIGHSCORE:
        displayHighscore()
        page = PAGE_TITLE        
    if page == PAGE_TEST:
        test()
        page = PAGE_TITLE

engine.tick()

