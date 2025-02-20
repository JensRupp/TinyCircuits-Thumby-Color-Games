from engine_nodes import EmptyNode, Text2DNode
import engine_link
import engine_draw
import time
from gaclib import helper
import engine
import engine_io
from engine_math import Vector2

if helper.is_simulator():
    print("import simulator")
    from gaclib import multiplayer_simulator
    baseclass = multiplayer_simulator.MultiplayerNodeSimulator
else:
    print("import viper")
    from gaclib import multiplayer_viper
    baseclass = multiplayer_viper.MultiplayerNodeViper


VERSION = "0.5"

HOSTMODE_RANDOM = 0
HOSTMODE_HOST = 1   #not implemented yet
HOSTMODE_CLIENT = 2 #not implemented yet

VALUE_BYTE = 0  # 1 byte
VALUE_WORD = 1  # 2 byte
VALUE_DWORD= 2  # 4 byte


VALUE_SIZE = [1,2,4]


class Value():
   def __init__(self, name: str, type, pos: int, count: int):
        super().__init__()
        self.name = name
        self.type = type
        self.pos = pos
        self.count = count
        
class MultiplayerNode(baseclass):
    

    def __init__(self, devicecount, localcount):
        super().__init__()
        self.log = None
        #should run before all other nodes
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

        #for synced data
        self.values = {}
        self.datapos = 0
        self.size = 0
        self.buffer = None
        
        #callback calling order
        # cb_identify_players: called during start screen
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
    
    #just stop the game but keep the connection
    #next game starts faster and the host does not switch
    def docancel(self):
        self.cancel = True
    
    #stop game and connection
    def stop(self):
        engine_link.stop()
        

    #start a multiplayer game
    def start(self):
        self.cancel = False
        self.synced = False
        if self.count > 1:
            nodecancel = Text2DNode(
                position=Vector2(0, 0),
                text=self.text_cancel.text,
                font=self.text_cancel.font,
                color=self.text_cancel.color,
                scale=self.text_cancel.scale,
                )
            helper.align_left(nodecancel, 0, self.width)
            helper.align_bottom(nodecancel, 0, self.height)
            self.add_child(nodecancel)
            
            
            if self.device_count > 1:
                if not engine_link.connected():
                    nodeconnecting = Text2DNode(
                        position=Vector2(0, 0),
                        text=self.text_connecting.text,
                        font=self.text_connecting.font,
                        color=self.text_connecting.color,
                        scale=self.text_connecting.scale,
                        )
                    self.add_child(nodeconnecting)
                    
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
                color=self.text_start.color,
                scale=self.text_start.scale,
                )
            self.add_child(nodestart)

            #add identifying labels to the start screen
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
                #send the complete initialized data to client        
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
        
    def clear(self):
        self.values = {}
        self.datapos = 0
        self.size = 0
        self.buffer = None

        
    #register synced data
    #returned value can be used as "handle" for faster access (pos parameter)   
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
        return v.pos
       
        
        
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
    
     
    def testvalue(self, n):
        self.write("test",n)
        v = self.read("test")
        print("Test "+ str(n)+" = "+str(v))
        assert v==n, "Value not equal"
        g1 = self.read("guard1")
        assert g1 == 42, "Guard 1"
        g2 = self.read("guard2")
        assert g2 == 66, "Guard 2"
        
 
    def testbuffer(self):
        testvalues = [[1,10, 100, 255],[1,10, 255, 256, 30000, 65535],[1,10,255,256,30000,65535,65536, 16777215, 16777216, 2147483647]]
        for kind in range (0,3):
            print("Kind "+str(kind))
            self.clear()
            self.register("guard1", VALUE_BYTE)
            self.register("test", kind)
            self.register("guard2", VALUE_BYTE)
        
            self.write("guard1",42)
            self.write("guard2",66)
    
            for test in testvalues[kind]:
              self.testvalue(test)                    
        self.clear()
    
    #without viper 5885
    #with viper    2719 initial code
    #              2234 optimzed read
    #              1808 optimied write
    #              1457 without calling extra function
    def testspeed(self):
        self.clear()
        self.device_count = 2
        self.local_count = 3
        self.count = self.device_count * self.local_count
    
        self.register("byte", VALUE_BYTE)
        self.register("word", VALUE_WORD)
        self.register("dword", VALUE_DWORD)
        self.register("bytep", VALUE_BYTE, True)
        self.register("wordp", VALUE_WORD, True)
        self.register("dwordp", VALUE_DWORD, True)
        
        start = time.ticks_ms()
        for count in range(0,1000):
            #print("count="+str(count))
            self.write("byte", count % 256)
            self.write("word", count % 65536)
            self.write("dword", count % 2147483648)
            for player in range(0, self.count):
                self.write_player("bytep",(count+player) % 256, player)
                self.write_player("wordp",(count+player) % 65536, player)
                self.write_player("dwordp", (count+player) % 2147483648, player)
            b = self.read("byte")
            assert b == count % 256, "byte"
            w = self.read("word")
            assert w == count % 65536, "word"
            dw = self.read("dword")
            assert dw == count % 2147483648, "dword"      
            for player in range(0, self.count):
                #print("player="+str(player))
                
                b = self.read_player("bytep", player)
                #print(str(b)+" = "+str(count % 256) )
                #print(self.debug())
                assert b == (count+player) % 256 , "bytep"
                w = self.read_player("wordp", player)
                assert w == (count+player) % 65536, "wordp"
                dw = self.read_player("dwordp", player)
                assert dw == (count+player) % 2147483648  , "dwordp"
        end = time.ticks_ms()
        duration = end-start
        print("Time: "+str(duration));
        
        self.clear()
        
    #test direct acccess, about twice the speed    
    def testspeed2(self):
        self.clear()
        self.device_count = 2
        self.local_count = 3
        self.count = self.device_count * self.local_count
        
    
        value_byte = self.register("byte", VALUE_BYTE)
        value_word = self.register("word", VALUE_WORD)
        value_dword = self.register("dword", VALUE_DWORD)
        value_bytep= self.register("bytep", VALUE_BYTE, True)
        value_wordp = self.register("wordp", VALUE_WORD, True)
        value_dwordp = self.register("dwordp", VALUE_DWORD, True)
        
        start = time.ticks_ms()
        for count in range(0,1000):
            self.write_byte(value_byte, count % 256)
            self.write_word(value_word, count % 65536)
            self.write_dword(value_dword, count % 2147483648)
            for player in range(0, self.count):
                self.write_byte_player(value_bytep,(count+player) % 256, player)
                self.write_word_player(value_wordp,(count+player) % 65536, player)
                self.write_dword_player(value_dwordp, (count+player) % 2147483648, player)
            
            b = self.read_byte(value_byte)
            assert b == count % 256, "byte"
            w = self.read_word(value_word)
            assert w == count % 65536, "word"
            dw = self.read_dword(value_dwordp)
            assert dw == count % 2147483648, "dword"      
            for player in range(0, self.count):
                #print("player="+str(player))
                
                b = self.read_byte_player(value_bytep, player)
                #print(str(b)+" = "+str(count % 256) )
                #print(self.debug())
                assert b == (count+player) % 256 , "bytep"
                w = self.read_word_player(value_wordp, player)
                assert w == (count+player) % 65536, "wordp"
                dw = self.read_dword_player(value_dwordp, player)
                assert dw == (count+player) % 2147483648  , "dwordp"
        end = time.ticks_ms()
        duration = end-start
        print("Time2: "+str(duration));
        
        self.clear()        

        
        
    