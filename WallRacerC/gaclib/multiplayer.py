from engine_nodes import EmptyNode, Text2DNode
import engine_link
import engine_draw
import time
from gaclib import helper
import engine
import engine_io
from engine_math import Vector2

VERSION = "0.3"

HOSTMODE_RANDOM = 0
HOSTMODE_HOST = 1   #not implemented yet
HOSTMODE_CLIENT = 2 #not implemented yet

MODE_LINK = 0
MODE_ONLINE = 1     #not implemented yet

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
   def __init__(self, name: str, type, pos, count):
        super().__init__()
        self.name = name
        self.type = type
        self.pos = pos
        self.count = count

cancel = False

def connected():
    global cancel
    # Clear anything that might not be related to the game
    engine_link.clear_send()
    engine_link.clear_read()
    cancel = False
def disconnected():
    global cancel
    cancel = True
        
class MultiplayerNode(EmptyNode):

    def __init__(self):
        super().__init__(self)
        
        self.layer = 0
        self.countdown = 5
        self.hostmode = HOSTMODE_RANDOM
        self.mode = MODE_LINK
        self.values = {}
        self.datapos = 0
        self.size = 0
        self.buffer = None
        self.host = False
        self.process = None
        #client callback
        #buffer contains data from last round or 0 at startup
        self.cb_client = None
        #host callback
        #call with the data from the client
        #host can process the data and add new values
        self.cb_host = None
        #called for host and client with the processed data
        self.cb_work = None
        # called once on the host in the start code to init the bufefr and send to the client
        self.cb_init = None
        
        self.text_connecting = None
        self.text_cancel = None
        self.text_start = None
        self.text_countdown = None
        
        self.position = Vector2(0,0)
        self.width = helper.SCREEN_WIDTH
        self.height = helper.SCREEN_HEIGHT
        
        self.synced = False
        self.counter = 0
        self.state = None
        self.player_count = 0 
        
        engine_link.set_connected_cb(connected)
        engine_link.set_disconnected_cb(disconnected)
    
    def running(self):
        global cancel
        return self.synced and (not cancel)
    def is_host(self):
        if self.player_count == 1:
            return True
        elif self.hostmode == HOSTMODE_RANDOM:
            return engine_link.is_host()
        else:
           return self.host
        
    def debug(self):
        r = ""
        for value in self.values.values():
            v=""
            for index in range(0,value.count):
                v=v+str(self.read(value.name,index))+','
            r = r + " "+ value.name +"("+str(value.type)+","+str(value.pos)+")="+str(self.read(value.name))
        return r
    
    def cancel(self):
        global cancel
        cancel = True
        
    def stop(self):
        engine_link.stop()
        
        
    def start(self, link = True):
        global cancel
        
        cancel = False

        if link:
            self.player_count = 2 
            
            self.synced = False
            nodeconnecting = Text2DNode(
                position=Vector2(0, 0),
                text=self.text_connecting.text,
                font=self.text_connecting.font,
                line_spacing=1,
                color=self.text_connecting.color,
                scale=self.text_connecting.scale,
                )
            self.add_child(nodeconnecting)
            
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
            
            engine_link.start()
            while not engine_link.connected() and (not cancel):
                if engine.tick():
                  if engine_io.MENU.is_just_pressed:
                      cancel = True

            nodeconnecting.mark_destroy()
             
            
            if cancel:
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

            
            while not cancel:
                if engine.tick():
                  if engine_io.MENU.is_just_pressed:
                      cancel = True
                  if engine_io.A.is_just_pressed:
                      break
                    
            nodestart.mark_destroy()
            nodecancel.mark_destroy()                   
            
            if cancel:
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
            
            while (count > 0) and (not cancel) :
     
                buffer[0] = 22 # just a marker, not used currently
                buffer[1] = count # currently not used 
                engine_link.send(buffer)
                
                # wait for the message from the other thumby
                while (engine_link.available() < 2) and (not cancel):
                    pass
                if engine_link.available() >= 2:
                    engine_link.read_into(buffer, 2)
                    time.sleep(1)
                
                    nodecountdown.text = str(count) 
                    engine.tick()            
                    count -= 1
                    
            
            nodecountdown.mark_destroy()
            
            if cancel:
                engine_link.stop()
                return False
            
            time.sleep(0.5)
            engine.tick() 
        
            if self.is_host():
                #engine_io.indicator(engine_draw.red)
                #host ini buffer and send
                if self.cb_init != None:
                    self.cb_init(self)
                engine_link.send(self.buffer)
            else:
                #engine_io.indicator(engine_draw.yellow)
                #client read init buffer
                while  engine_link.available() < self.size:
                    pass
                engine_link.read_into(self.buffer, self.size)
            #engine_io.indicator(engine_draw.green)
                     
            self.synced = True
            return True
        else:
            #singleplayer
            self.player_count = 1 
            if self.cb_init != None:
                self.cb_init(self)
            
            self.synced = True
            
            return True
            
    def register(self,name: str, type, count=1):
        v = Value(name,type,self.datapos, count)
        self.values[name] = v
        self.datapos += VALUE_SIZE[type] * count
        self.size += VALUE_SIZE[type] * count
        self.buffer = bytearray(self.size)
        return v.pos
    
       
    @micropython.viper    
    def write_byte(self, pos = int ,value = int):
        self.buffer[pos] = int(value) & 0b11111111
        
    @micropython.viper    
    def write_word(self, pos = int,value = int):
        p = int(pos)
        v = int(value)
        self.buffer[pos] = v & 0b11111111
        self.buffer[p+1] = (v >> 8) & 0b11111111
            
    def write(self, name, value, index = 0):
        v = self.values[name]
        pos = v.pos + VALUE_SIZE[v.type] * index
        if v.type == VALUE_BYTE:
            self.write_byte(pos, value)
        elif v.type == VALUE_WORD:
            self.write_word(pos, value)
            
                                    
    @micropython.viper
    def read_byte(self, pos = int) -> int:
        return int(self.buffer[pos])
    
    @micropython.viper
    def read_word(self, pos = int) -> int:
        p = int(pos)
        v = int(self.buffer[p])
        x = int(self.buffer[p+1])
        v = int(v + (x << 8 ))
        return v
    
    def read(self,name,index = 0):
        v = self.values[name]
        pos = v.pos + VALUE_SIZE[v.type] * index
        if v.type == VALUE_BYTE:
            return self.read_byte(pos) 
        elif v.type == VALUE_WORD:
            return self.read_word(pos)
        
    def tick(self, dt):
        global cancel
        if self.player_count == 2:
            if self.synced and engine_link.connected() and (not cancel):
                if self.is_host():
                    #wait for data from client
                    while  engine_link.available() < self.size:
                        pass
                    engine_link.read_into(self.buffer, self.size)
                    if self.cb_host != None:
                        self.cb_host(self)  

                    engine_link.send(self.buffer)
                    
                    if self.cb_work != None:
                        self.cb_work(self)                  

                else:
                    if self.cb_client != None:
                        self.cb_client(self)
                    engine_link.send(self.buffer)
                    while engine_link.available() < self.size:
                        pass
                        
                    engine_link.read_into(self.buffer, self.size)
                    if self.cb_work != None:
                        self.cb_work(self)
        else:
            if self.cb_host != None:
                self.cb_host(self)  
            if self.cb_work != None:
                self.cb_work(self)
        self.counter += 1
    
 
        
        
    