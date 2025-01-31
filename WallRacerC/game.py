import random
import framebuf
import time
import math

import engine
import engine_io
import engine_draw
import engine_link
from engine_math import Vector2
from engine_nodes import Text2DNode, Sprite2DNode
from engine_resources import TextureResource

from bonusdots import BonusDots
from explosion import Explosion

from gaclib import helper
from gaclib import multiplayer

BONUS_FACTOR = 20  # points for collecting a bonus dot multiplied by speed

BOOST_TIME = 40  # number of pixels to boost
BOOST_SPEED = 4  # increase of speed during boost
BOOST_RUMBLE = 0.2  # rumble intensity during boost
BOOST_COOLDOWN = 20

START_BORDER_DISTANCE = 30

# map direction to offsets
PLAYERXADD = [1, 0, -1, 0]  # mapping of direction to x add
PLAYERYADD = [0, 1, 0, -1]  # mapping of direction to y add

#Define Colors
FRAME1 = engine_draw.white.value
FRAME2 = engine_draw.red.value
BONUS = engine_draw.white.value
FPS = engine_draw.yellow.value
TEXT = engine_draw.white.value
BACKGROUND = engine_draw.black.value
#LIGHT MEDIUM DARK
#GREEN, BLUE, RED, ORANGE, VIOLET, TURQUOISE
PLAYER_COLOR=[[0xbff7, 0x8c7f, 0xfcd3, 0xfead, 0xfa9f, 0x1ffc], [0x07e0, 0x001F, 0xF800,  0xFDA0, 0xb817, 0x05b4], [0x0540, 0x18f2, 0xa800, 0xbc40, 0x9813, 0x034c]]

FPSAVERAGECOUNT = 30

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

#get position of all player in an array   
def allplayerpos(multi):
    p = []
    for player in range(0, multi.count):
        x = multi.read("x")
        y = multi.read("y")
        p.append([x,y])
    return p    

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
                                font=multi.state.font6,
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
    #multi.log.log("cbinitgame")
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
        
    if multi.state.hasbonusdots:       
        multi.state.bonusdots.init(allplayerpos(multi))
    #multi.log.log("cbinitgame done")
    


def cbinitplayer(multi, player):
    #multi.log.log("cbinitplayer")    
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
    #multi.log.log("cbinitplayer "+multi.debug())    
    
       
def cbplayer(multi, player):
    #multi.log.log("cbplayer")    
    
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

                if multi.state.hasbonusdots: 
                    hit = multi.state.bonusdots.check(x, y, multi.state.screen)
                    if hit:
                        multi.state.bonusdots.add(allplayerpos(multi))
                        speed = multi.read("speed")
                        bonus_points = speed * BONUS_FACTOR
                        points += points
                        multi.state.displayBonus(bonus_points)

                if multi.state.screen.pixel(x, y) != BACKGROUND:
                    multi.write_player("c", 1, player)

                multi.write_player("p", points, player)
    #multi.log.log("cbplayer "+multi.debug())    
                

#not used
def cbwork(multi):
    pass


def cbdisplay(multi):
    #multi.log.log("cbdisplay "+multi.debug())    
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
            multi.state.explosion.add(x,y)
            multi.write_player("c", 2, player)
        #center on this player
        if multi.state.width > helper.SCREEN_WIDTH:
            if player == this:
                screenx = helper.SCREEN_WIDTH - x
                screeny = helper.SCREEN_HEIGHT - y
                multi.state.arena.position = Vector2(screenx, screeny)

    if multi.state.hasbonusdots:
        multi.state.bonusdots.draw_all(multi.counter, multi.state.screen)


    if multi.state.explosion.move(multi.state.screen):
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
    #multi.log.log("cbdisplay done")    



class Game():
    def __init__(self,devicecount, localcount, width, height, speed, hasbonusdots, hasboost, showfps, font6, font16, log):
        self.width = width
        self.height = height
        self.speed = speed
        self.log = log
        
        self.won = -1
        
        self.screen = None
        self.arena = None
        # for explosions
        self.explosion = Explosion(self.width, self.height)
        # for bonus points
        self.hasbonusdots = hasbonusdots
        self.bonusdots = BonusDots(self.width, self.height)
        
        # for bonus point display
        self.sleep = 0
        self.bonus1 = None
        self.bonus2 = None
        
        #for identify
        self.idplayer = [None, None, None]

        #for boost
        self.hasboost = hasboost
        self.boost = 0
        
        #for player control
        self.control = []
        
        #for FPS display
        self.showfps = showfps
        self.fpscount = FPSAVERAGECOUNT
        self.fpssum = 0
        self.fpsnode= None
        
        self.multi = None
        self.devicecount = devicecount
        self.localcount = localcount
        
        self.font6 = font6
        self.font16 = font16
        
        


    def addFPS(self):
        if self.showfps:
            self.fpsnode =  Text2DNode(
              position=Vector2(0, 0),
              text="FPS",
              font=self.font16,
              color=FPS,
              scale=Vector2(1, 1),
              layer=100
            )
            helper.align_top(self.fpsnode)
            helper.align_left(self.fpsnode)

    def updateFPS(self):
        if self.showfps:
            fps = engine.get_running_fps()
            self.fpssum += fps
            self.fpscount -= 1
            if self.fpscount == 0:
                self.fpsnode.text = str(int(self.fpssum // FPSAVERAGECOUNT))
                #helper.align_left(fpsnode)
                self.fpssum = 0
                self.fpscount = FPSAVERAGECOUNT

    # draw a frame with alternating colors
    def drawFrame(self):
        self.screen.rect(0, 0, self.width , self.height , FRAME1)

        lw = int(helper.SCREEN_WIDTH / 4)
        c = int((self.width / (lw * 2)) )
        for step in range(c):
            self.screen.hline(lw + step * lw * 2, 0, lw, FRAME2)
            self.screen.hline(lw + step * lw * 2, self.height - 1, lw, FRAME2)

        w = int(helper.SCREEN_HEIGHT / 4)
        c = int((self.height / (lw * 2)) )
        for step in range(c):
            self.screen.vline(0, lw + step * lw * 2, lw, FRAME2)
            self.screen.vline(self.width - 1, lw + step * lw * 2, lw, FRAME2)
    
    def initScreen(self):
        texture = TextureResource(self.width, self.height,0,16)
        self.screen = framebuf.FrameBuffer(texture.data, texture.width, texture.height, framebuf.RGB565)
        
        # Clear virtual screen
        self.screen.fill(BACKGROUND)
        # Add the frame
        self.drawFrame()
        self.arena = Sprite2DNode(texture=texture)
        
    def finishScreen(self):    
        self.arena.mark_destroy()
    
    
    #display the bonus
    def displayBonus(self, points):
        self.bonus1 = Text2DNode(
            position=Vector2(0, -20),
            text="Bonus!",
            font=self.font16,
            line_spacing=1,
            color=BONUS,
            scale=Vector2(2, 2),
            layer = 100
        )

        self.bonus2 = Text2DNode(
            position=Vector2(0, 20),
            text=str(points),
            font=self.font16,
            line_spacing=1,
            color=BONUS,
            scale=Vector2(2, 2),
            layer = 100
        )
        #display for a short time
        self.sleep =  engine.fps_limit() // 2


    
    
    def play(self):
        engine.fps_limit(120)

        self.multi = multiplayer.MultiplayerNode(self.devicecount, self.localcount)
        self.multi.log = self.log
        self.multi.text_connecting = helper.Text("Connecting", self.font16,Vector2(1, 1), TEXT  )
        self.multi.text_cancel = helper.Text("M to cancel", self.font6,Vector2(1, 1), TEXT  )
        self.multi.text_start = helper.Text(" Press\n    A\nto start", self.font16,Vector2(1, 1), TEXT  )
        self.multi.text_countdown = helper.Text("Ready",self.font16,Vector2(2, 2), TEXT )
        self.multi.countdown = 2
        self.multi.state = self
        
       
        #init controls    
        if self.localcount == 1:
            self.control.append(control1)
            self.control.append(control1)
        elif self.localcount == 2:    
            self.control.append(control2)
            self.control.append(control3)
            self.control.append(control2)
            self.control.append(control3)
        elif self.localcount == 3:    
            self.control.append(control4)
            self.control.append(control5)
            self.control.append(control6)
            self.control.append(control4)
            self.control.append(control5)
            self.control.append(control6)

        #set boost
        if self.hasboost:
            self.boost = -BOOST_COOLDOWN  # start with charging
            if self.localcount == 1:
                engine_io.indicator(engine_draw.blue)

        self.multi.register("speed", multiplayer.VALUE_BYTE)
        self.multi.register("x", multiplayer.VALUE_WORD, True)
        self.multi.register("y", multiplayer.VALUE_WORD, True)
        self.multi.register("d", multiplayer.VALUE_BYTE, True)
        self.multi.register("t", multiplayer.VALUE_BYTE, True)
        self.multi.register("c", multiplayer.VALUE_BYTE, True)    
        self.multi.register("b", multiplayer.VALUE_BYTE, True)    
        self.multi.register("p", multiplayer.VALUE_DWORD, True)
        
        self.multi.cb_init_game = cbinitgame
        self.multi.cb_init_player = cbinitplayer
        self.multi.cb_identify_players = cbidentifyplayers

        self.log.info("Start")
        if self.multi.start():

            self.multi.cb_player = cbplayer
            self.multi.cb_display = cbdisplay
            
            self.addFPS()
            self.initScreen()
            
            self.log.info("Loop")
            while self.multi.running():
                if engine.tick():
                    self.log.info("Tick")

                    self.updateFPS()

            self.multi.cb_player = None
            self.multi.cb_display = None

            self.finishScreen()
            
            won = self.multi.state.won
            if self.won >= 0:
                points = self.multi.read_player("p", self.won)
            else:
                points = 0 
                
            if self.showfps:
                self.fpsnode.mark_destroy()
        else:
            points = 0
            won = -1;

        #remove any messages that might be left
        engine_link.clear_send()
        engine_link.clear_read()

        self.multi.mark_destroy()
        engine_io.rumble(0)

        return won, points
        
        
    
