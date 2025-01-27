from engine_nodes import EmptyNode, Text2DNode
import engine_link
import engine_draw
import time
from gaclib import helper
import engine
import engine_io
from engine_math import Vector2

VERSION = "0.4"

HOSTMODE_RANDOM = 0
HOSTMODE_HOST = 1   #not implemented yet
HOSTMODE_CLIENT = 2 #not implemented yet

VALUE_BYTE = 0  # 1 byte
VALUE_WORD = 1  # 2 byte
VALUE_FLOAT = 2 # x byte not implemented yet
VALUE_STR3 = 3 # 3 byte not implemented yet
VALUE_STR8 = 4 # 8 byte not implemented yet
VALUE_STR16 = 5 # 16 byte not implemented yet

VALUE_SIZE = [1,2,4,3,8,16]

#logfile = open("/Games/MultiTest/MultiTest.log", "a")
def log(msg):
    pass
    #global logfile
    #xmsg = str(time.ticks_ms()) + ": " + msg
    #logfile.write(xmsg + "\n")
    #logfile.flush()

class Value():
   def __init__(self, name: str, type, pos: int, count: int):
        super().__init__()
        self.name = name
        self.type = type
        self.pos = pos
        self.count = count
        
class MultiplayerNode(EmptyNode):

    def __init__(self, devicecount, localcount):
        super().__init__(self)
        #should run before all other nodes
        self.log = None
        self.layer = 0
        #fullscreen
        self.position = Vector2(0,0)
        self.width = helper.SCREEN_WIDTH
        self.height = helper.SCREEN_HEIGHT
        
        # number of devices
        # 1 or 2 linked by cable
        self.device_count = devicecount
        # number of players on one thumby
        self.local_count = localcount
        # total number of players
        # numbering is first local then device
        # player numbers are 0 to count-1
        self.count = devicecount * localcount

        # for now always random
        self.hostmode = HOSTMODE_RANDOM

        self.countdown = 5
        self.host = False

        #for synced data
        self.values = {}
        self.datapos = 0
        self.size = 0
        self.buffer = None
        
        #callback calling order
        #
        # cb_init_game: once at start of game on the host thumby
        # cb_init_player: once per player at start of game
        # loop
        #   cb_player: once per tick for every player 
        #   cb_work: once per tick  on the host thumby
        #   cb_display: once per tick for every thumby
        
        #callback cb_init_game(self)
        #called once at start of game on the host thumby
        self.cb_init_game = None
        
        #callback cb_init_player(self, number)
        #called once per player at start of game with the data from cb_init_game and the player number
        self.cb_init_player = None
        
        #callback cb_player(self, number)
        #called once per tick for every player 
        self.cb_player = None
                  
        #callback cb_work(self)
        #called once per tick  on the host thumby
        self.cb_work = None
        
        #callback cb_display(self)
        # called once per tick for every thumby
        self.cb_display  = None
        
        #callback cb_identify_players(self, create)
        #called in the Start screen to add player identification
        # create = true -> create node
        # create = false -> destroy nodes
        self.cb_identify_players = None

        #text for start
        self.text_connecting = None
        self.text_cancel = None
        self.text_start = None
        self.text_countdown = None
        
        #connection state
        self.synced = False
        #counter increased once per tick
        self.counter = 0
        #game can store custom data here
        self.state = None
        
        engine_link.set_connected_cb(self.connected)
        engine_link.set_disconnected_cb(self.disconnected)
        
    def connected(self):
        # Clear anything that might not be related to the game
        engine_link.clear_send()
        engine_link.clear_read()
        self.cancel = False
    def disconnected(self):
        #when the connection is lost stop game on all thumbies
        self.cancel = True
    
    def running(self):
        return self.synced and (not self.cancel)
    
    def is_host(self):
        if self.device_count == 1:
            return True
        elif self.device_count == 2:
            return engine_link.is_host()
        
    def debug(self):
        r = ""
        for value in self.values.values():
            v=""
            for index in range(0,value.count):
                if index>0:
                    v=v+","
                v=v+str(self.read_player(value.name,index))
            r = r + " "+ value.name +"("+str(value.type)+","+str(value.pos)+")="+v
        return r
    
    def docancel(self):
        self.cancel = True
        
    def stop(self):
        engine_link.stop()
        
        
    def start(self):
        
        self.cancel = False
        self.synced = False
        if self.count > 1:
            nodecancel = Text2DNode(
                position=Vector2(0, 0),
                text=self.text_cancel.text,
                font=self.text_cancel.font,
                line_spacing=1,
                color=self.text_cancel.color,
                scale=self.text_cancel.scale,
                )
            helper.align_left(nodecancel, 0, self.width)
            helper.align_bottom(nodecancel, 0, self.height)
            self.add_child(nodecancel)
            
            
            if self.device_count > 1:
                nodeconnecting = Text2DNode(
                    position=Vector2(0, 0),
                    text=self.text_connecting.text,
                    font=self.text_connecting.font,
                    line_spacing=1,
                    color=self.text_connecting.color,
                    scale=self.text_connecting.scale,
                    )
                self.add_child(nodeconnecting)
                
                
                if engine_link.connected():
                    #if already connected clear all the buffers
                    #engine_link.clear_send()
                    #engine_link.clear_read()
                    pass
                else:
                    engine_link.start()
                while not engine_link.connected() and (not self.cancel):
                    if engine.tick():
                        if engine_io.MENU.is_just_pressed:
                            self.cancel = True

                nodeconnecting.mark_destroy()
             
                if self.cancel:
                    engine_link.stop()
                    return False
            
            nodestart = Text2DNode(
                position=Vector2(0, 0),
                text=self.text_start.text,
                font=self.text_start.font,
                line_spacing=1,
                color=self.text_start.color,
                scale=self.text_start.scale,
                )
            self.add_child(nodestart)

            if self.cb_identify_players != None:
                self.cb_identify_players(self, True)

            while not self.cancel:
                if engine.tick():
                  if engine_io.MENU.is_just_pressed:
                      self.cancel = True
                  if engine_io.A.is_just_pressed:
                      break
                    

            if self.cb_identify_players != None:
                self.cb_identify_players(self, False)
                    
                    
            nodestart.mark_destroy()
            nodecancel.mark_destroy()                   
            
            if self.cancel:
                engine_link.stop()
                return False        
            
            buffer = bytearray(2)
            count = self.countdown

            nodecountdown = Text2DNode(
                position=Vector2(0, 0),
                text=self.text_countdown.text,
                font=self.text_countdown.font,
                line_spacing=1,
                color=self.text_countdown.color,
                scale=self.text_countdown.scale,
                )
            self.add_child(nodecountdown)
            
            time.sleep(0.5)
            engine.tick() #display the text
            
            while (count > 0) and (not self.cancel) :
     
                buffer[0] = 22 # just a marker, not used currently
                buffer[1] = count # currently not used 
                
                if self.device_count > 1:
                    engine_link.send(buffer)
                    
                    # wait for the message from the other thumby
                    while (engine_link.available() < 2) and (not self.cancel):
                        pass
                    if engine_link.available() >= 2:
                        engine_link.read_into(buffer, 2)
                        time.sleep(1)
                    
                        nodecountdown.text = str(count) 
                        engine.tick()            
                        count -= 1
                else:
                    time.sleep(1)
                    nodecountdown.text = str(count) 
                    engine.tick()            
                    count -= 1                    
                    
            
            nodecountdown.mark_destroy()
            
            if self.cancel:
                if self.decice_count > 1:
                    engine_link.stop()
                return False
            
            time.sleep(0.5)
            engine.tick() 
        
            if self.is_host():
                if self.cb_init_game != None:
                    self.cb_init_game(self)
                if self.device_count>1:    
                    engine_link.send(self.buffer)                        

                    while  engine_link.available() < self.size:
                        pass
                    engine_link.read_into(self.buffer, self.size)
                
                for number in range(0, self.local_count):
                    if self.cb_init_player != None:
                        self.cb_init_player(self, number)
                #send the complelty initialized data to client        
                if self.device_count>1:    
                    engine_link.send(self.buffer)                                                
            else:
                while  engine_link.available() < self.size:
                    pass
                engine_link.read_into(self.buffer, self.size)
                                
                for number in range(self.local_count, self.local_count*2):
                    if self.cb_init_player != None:
                        self.cb_init_player(self, number)

                engine_link.send(self.buffer)
                
                while  engine_link.available() < self.size:
                    pass
                engine_link.read_into(self.buffer, self.size)
            self.synced = True
            return True
        else:
            #singleplayer
            if self.cb_init_game != None:
                self.cb_init_game(self)
            if self.cb_init_player != None:
                self.cb_init_player(self, 0)
            self.synced = True
            return True
            
    def register(self,name: str, type: int, player: bool = False):
        if player:
            count = self.count
        else:
            count = 1
        v = Value(name,type,self.datapos, count)
        self.values[name] = v
        self.datapos += VALUE_SIZE[type] * count
        self.size += VALUE_SIZE[type] * count
        self.buffer = bytearray(self.size)
       
    @micropython.viper    
    def write_byte(self, pos: int ,value: int):
        self.buffer[pos] = int(value) & 0b11111111
        
    @micropython.viper    
    def write_word(self, pos: int,value: int):
        p = int(pos)
        v = int(value)
        self.buffer[pos] = v & 0b11111111
        self.buffer[p+1] = (v >> 8) & 0b11111111
    
    @micropython.viper            
    def write(self, name, value):
        v = self.values[name]
        if v.type == VALUE_BYTE:
            self.write_byte(v.pos, value)
        elif v.type == VALUE_WORD:
            self.write_word(v.pos, value)
            
    @micropython.viper            
    def write_player(self, name, value, index):
        v = self.values[name]
        pos = int(v.pos) + int(VALUE_SIZE[v.type]) * int(index)
        if v.type == VALUE_BYTE:
            self.write_byte(pos, value)
        elif v.type == VALUE_WORD:
            self.write_word(pos, value)            

    @micropython.viper
    def read_byte(self, pos: int) -> int:
        return int(self.buffer[pos])
    
    @micropython.viper
    def read_word(self, pos: int) -> int:
        p = int(pos)
        v = int(self.buffer[p])
        x = int(self.buffer[p+1])
        v = int(v + (x << 8 ))
        return v
    
    @micropython.viper            
    def read(self,name):
        v = self.values[name]
        pos = v.pos 
        if v.type == VALUE_BYTE:
            return self.read_byte(pos) 
        elif v.type == VALUE_WORD:
            return self.read_word(pos)
        
    @micropython.viper            
    def read_player(self, name, player):
        v = self.values[name]
        pos = int(v.pos) + int(VALUE_SIZE[v.type]) * int(player)
        if v.type == VALUE_BYTE:
            return self.read_byte(pos) 
        elif v.type == VALUE_WORD:
            return self.read_word(pos)
        
        
    def tick(self, dt):
        if self.device_count > 1:
            if self.synced and engine_link.connected() and (not self.cancel):
                if self.is_host():
                    #wait for data from client
                    while  engine_link.available() < self.size:
                        pass
                    engine_link.read_into(self.buffer, self.size)
                    
                    for number in range(0, self.local_count):
                        if self.cb_player != None:
                            self.cb_player(self, number)
    
                    if self.cb_work != None:
                        self.cb_work(self)

                    engine_link.send(self.buffer)
                    
                    if self.cb_display != None:
                        self.cb_display(self)                  
                else:
                    for number in range(self.local_count, self.local_count*2):
                        if self.cb_player != None:
                            self.cb_player(self, number)
                    
                    engine_link.send(self.buffer)
                    while engine_link.available() < self.size:
                        pass
                        
                    engine_link.read_into(self.buffer, self.size)

                    if self.cb_display != None:
                        self.cb_display(self)                  
        else:
            for number in range(0, self.local_count):
                if self.cb_player != None:
                    self.cb_player(self, number)
            if self.cb_work != None:
                self.cb_work(self)
            if self.cb_display != None:
                self.cb_display(self)                  
        self.counter += 1
    
 
        
        
    