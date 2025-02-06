import engine_main
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
from gaclib import menu

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
        position=Vector2(0, -48),
        texture=logo,
    )

    help = helper.Text("A Select B Back",font6,Vector2(1, 1),YELLOW)
    info = helper.Text("Info",font6,Vector2(1, 1), YELLOW)
    menuformat = menu.MenuFormat(font16, Vector2(1, 1),WHITE, GREEN)

    start = []
    start.append(menu.Menu("1 Player", 11, None))
    start.append(menu.Menu("2 Players", 12, None))
    start.append(menu.Menu("3 Players", 13, None))

    hostlink = []
    hostlink.append(menu.Menu("Link 1v1", 21, None))
    hostlink.append(menu.Menu("Link 2v2", 22, None))
    hostlink.append(menu.Menu("Link 3v3", 23, None))

    menuitems = []
    menuitems.append(menu.Menu("Start Game", 1, start))
    menuitems.append(menu.Menu("Host Game", 2, hostlink))
    menuitems.append(menu.Menu("Join Game", 3, None))
    menuitems.append(menu.Menu("Options", 4, None))
    menuitems.append(menu.Menu("Highscore", 5, None))
    menuitems.append(menu.Menu("Test", 6, None))


    menunode = menu.MenuNode(Vector2(0,0), helper.SCREEN_WIDTH, 92, help, info, menuformat, menuitems)
    helper.align_bottom(menunode)

    page = 0

    while menunode.selection==0:
        if engine.tick():
            pass
        
    if menunode.selection == -1:
        page = PAGE_QUIT
    elif 11 <= menunode.selection <= 13:
        page = PAGE_GAME
    elif 21 <= menunode.selection <= 23:
        page = PAGE_GAME
    elif menunode.selection == 3:
        page = PAGE_GAME
    elif menunode.selection == 4:
        page = PAGE_OPTIONS
    elif menunode.selection == 5:
        page = PAGE_HIGHSCORE 
    elif menunode.selection == 6:
        page = PAGE_TEST
    else:
        page = PAGE_QUIT
        
    logo_node.mark_destroy()
    menunode.mark_destroy_all()
    
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
#     multi = multiplayer.MultiplayerNode(1, 1)
#     multi.testbuffer()
#     multi.testspeed()
#     multi.testspeed2()
#     multi.mark_destroy
# 
#     
#     
#     nodes = []
#     for x in range(0,3):
#         for y in range(0,6):
#             c = PLAYER_COLOR[x][y]
#             position = Vector2(x*21-64+10,y*21-64+10)
#             node = Rectangle2DNode(position,20,20, c)
#             nodes.append(node)
#     
#     while True:
#         if engine.tick():
#             if engine_io.A.is_just_pressed:
#                 break
#     for node in nodes:
#         node.mark_destroy()
    help = helper.Text("A Select B Back",font6,Vector2(1, 1),YELLOW)
    info = helper.Text("Info",font6,Vector2(1, 1), YELLOW)
    menuformat = menu.MenuFormat(font16, Vector2(1, 1),WHITE, GREEN)
    
    
    sub11 = []
    sub11.append(menu.Menu("O 1-1-1", 111, None))
    sub11.append(menu.Menu("O 1-1-2", 112, None))
    
    sub12 = []
    sub12.append(menu.Menu("O 1-2-1", 121, None))
    sub12.append(menu.Menu("O 1-2-2", 122, None))
    
    
    sub1 = []
    sub1.append(menu.Menu("O 1-1", 11, sub11))
    sub1.append(menu.Menu("O 1-2", 12, sub12))
    sub1.append(menu.Menu("O 1-3", 13, None))
    
    sub2 = []
    sub2.append(menu.Menu("O 2-1", 21, None))
    sub2.append(menu.Menu("O 2-2", 22, None))
    sub2.append(menu.Menu("O 2-3", 23, None))

    menuitems = []
    menuitems.append(menu.Menu("Option 1", 1, sub1))
    menuitems.append(menu.Menu("Option 2", 2, sub2))
    menuitems.append(menu.Menu("Option 3", 3, None))
    menuitems.append(menu.Menu("Option 4", 4, None))
    menuitems.append(menu.Menu("Option 5", 5, None))
    menuitems.append(menu.Menu("Option 6", 6, None))

    menunode = menu.MenuNode(Vector2(0,0), helper.SCREEN_WIDTH, 100, help, info, menuformat, menuitems)
    helper.align_bottom(menunode)
    x = menunode.show()
    print(x)
    menunode.mark_destroy_all()
    
            
    

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

