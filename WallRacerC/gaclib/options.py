import engine
import engine_io
from gaclib import table
from engine_nodes import EmptyNode,Rectangle2DNode, Text2DNode
from engine_math import Vector2
from engine_resources import FontResource
from engine_draw import Color, set_background_color
from math import ceil
from gaclib import helper
import json


SCREEN_WIDTH = 128
SCREEN_HEIGHT = 128

MODE_OPTIONS = 0
MODE_HELP = 1

#A class for the settings of the options list
class OptionsFormat():
    def __init__(self, font: FontResource, scale: Vector2, color: Color, selected: Color, split: int):
        self.font = font
        self.scale = scale
        self.color = color
        self.selected = selected
        self.split = split
        
#A single value thet can be selected in a option        
class OptionsValue():
    def __init__(self, text: str, id):
        self.text = text
        self.id = id    

#One option to select from
#text: the text to display
#help: help text displayed when pressing B while the option is selected
#id: id of the option used to store the setting in the data map
#values: list of GacOptionsValue
#default: default value used for this option, this  is the id from the values list        
class OptionsItem():
    def __init__(self, text: str, help: str, id, values, default, refresh = False, conditions = []):
        self.text = text
        self.help = help
        self.id = id
        self.default = default
        self.values = values
        self.conditions = conditions
        self.refresh = refresh
    
    #find the index of the currently selected value
    def getindex(self,data):
        v = data.get(self.id)
        for index in range(len(self.values)):
            if self.values[index].id == v:
                return index
        return 0    
            
    #return the string of the current value for thos option    
    def getvalue(self, data):
        return self.values[self.getindex(data)].text
    
    #select the next value in the values list
    def incvalue(self, data):
        v = self.getindex(data)
        if v < len(self.values) -1:
            v = v + 1
        else:
            v = 0
        data[self.id] = self.values[v].id    

    #select the previous value in the values list
    def decvalue(self, data):
        v = self.getindex(data)
        if v > 0:
            v = v - 1
        else:
            v = len(self.values) - 1
        data[self.id] = self.values[v].id    
        
                
#main class to display the options        
class OptionsNode(EmptyNode):
    def __init__(self, titletext: helper.Text, helptext: helper.Text, infotext: helper.Text, listformat: OptionsFormat, background: Color, data):
        super().__init__(self)
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.position = Vector2(0, 0)
        self.title = titletext
        self.help = helptext
        self.info = infotext
        self.list = listformat
        self.options = []
        self.background = background
        self.data = data
        self.mode = MODE_OPTIONS
        self.quit = False
        
        self.init()
        
    def clear(self):
        self.titlenode = None
        self.helpnode = None
        self.infonode = None
        self.table = None
        self.mark_destroy_children()
            
    def addoption(self, text, help, id, value, default, refresh = False, conditions = []):
        item = OptionsItem(text, help, id, value, default, refresh, conditions)
        self.options.append(item)
        
    def load(self, filename):
        optionstext = open(filename,'r').read()
        options = json.loads(optionstext)
        optionslist = options["options"]
        for option in optionslist:
            values = []
            for v in option["values"]:
                values.append(OptionsValue(v[0],v[1]))
                
            help = helper.word_wrap(option["help"], self.list.font, self.list.font, self.width)
                
            self.addoption(option["text"], help, option["id"], values, option["default"], option["refresh"], option["conditions"])
          
        
    def callback(self):
        self.infonode.text = str(self.table.selectedrow+1)+"/"+str(len(self.table.rows))+"\n"+self.info.text
        helper.align_right(self.infonode)
           
    def initoptions(self):
        set_background_color(self.background)

        columns = [table.Column(self.list.split), table.Column(128-self.list.split)]
        height = self.height - (self.titlenode.height + 4 + self.helpnode.height + 4)
        self.table = table.TableNode(Vector2(0,0), self.width, height, self.list.font, self.list.scale, self.list.color, columns, 2)
        self.table.selcolor = self.list.selected
        self.table.selection = table.SELECTION_ROW
        self.table.callback = self.callback
        helper.align_top(self.table, self.titlenode.height + 4)


        for index, option in enumerate(self.options):
            if len(option.conditions) > 0:
                orcheck = False
                for orcond in option.conditions:
                    andcheck = True
                    for andcond in orcond:
                        v = self.data[andcond[0]]
                        if v != andcond[1]:
                            andcheck = False
                    orcheck = orcheck or andcheck
            else:
                orcheck = True
            if orcheck:
                self.data.setdefault(option.id, option.default)
                row = [option.text, option.getvalue(self.data)]
                self.table.add_row(row, index)

        self.add_child(self.table)
            
           
    def init(self):
        self.titlenode = Text2DNode(Vector2(0,0),
                           self.title.font,
                           self.title.text,
                           0,
                           self.title.scale,
                           1,
                           1,
                           1,
                           self.title.color,
                           2)
        helper.align_top(self.titlenode)
        self.listtop = self.titlenode.height + 4 - self.height / 2
        self.add_child(self.titlenode)
        
        self.helpnode = Text2DNode(Vector2(0,0),
                           self.help.font,
                           self.help.text,
                           0,
                           self.help.scale,
                           1,
                           1,
                           1,
                           self.help.color,
                           2)
        helper.align_left(self.helpnode)
        helper.align_bottom(self.helpnode)
        self.listbottom = self.helpnode.position.y - self.helpnode.height // 2  
        self.add_child(self.helpnode)


        s = "__/__\n"+self.info.text
        self.infonode = Text2DNode(Vector2(0,0),
                           self.info.font,
                           s,
                           0,
                           self.info.scale,
                           1,
                           1,
                           1,
                           self.info.color,
                           2)
        helper.align_right(self.infonode)
        helper.align_bottom(self.infonode)
        
        if (self.infonode.position.y - 2) < self.listbottom:
            self.listbotom = self.infonode.position.y - 2
        
        self.add_child(self.infonode)
        
        
        if (self.infonode.position.y - 2) < self.listbottom:
            self.listbotom = self.infonode.position.y - 2
         
    def refresh(self):
        selectedrow = self.table.selectedrow
        selectedcol = self.table.selectedcol
        self.clear()
        self.init()
        self.initoptions()
        self.table.selectedrow = selectedrow
        self.table.selectedcol = selectedcol
         
    def initHelp(self,text):
        #remember selection
        self.selectedrow = self.table.selectedrow
        self.selectedcol = self.table.selectedcol
        self.clear()
        self.helptextnode = Text2DNode(Vector2(0,0),
           self.list.font,
           text,
           0,
           self.list.scale,
           1,
           0,
           0,
           self.list.color,
           2)
        helper.align_left(self.helptextnode)
        helper.align_top(self.helptextnode)
        
        self.helptop = self.helptextnode.position.y
        self.helpbottom = self.helptop - self.helptextnode.height + self.height
                                    
        self.footertext = Text2DNode(Vector2(0,0),
           self.help.font,
           "U/D Scroll B Back",
           0,
           self.help.scale,
           1,
           1,
           1,
           self.help.color,
           6)
        
        self.footerbox = Rectangle2DNode(Vector2(0,0),
                                         self.width,
                                         self.footertext.height + 2,
                                         self.background,
                                         1,
                                         False,
                                         0,
                                         Vector2(1,1),
                                         5)
        helper.align_bottom(self.footerbox)
        helper.align_left(self.footertext)
        helper.align_bottom(self.footertext)
        
    def modeOptions(self):
        if engine_io.A.is_just_pressed:
            self.quit = True
        if engine_io.B.is_just_pressed:
            s = self.options[self.table.get_id()].help
            if not (s == ""):
                self.initHelp(s)
                self.mode = MODE_HELP
                engine_io.release_all_buttons()
        if engine_io.RIGHT.is_pressed_autorepeat:
            self.options[self.table.get_id()].incvalue(self.data)
            self.table.set_text(1,self.table.selectedrow,self.options[self.table.get_id()].getvalue(self.data))
            
            if self.options[self.table.get_id()].refresh:
                self.refresh()
            
            self.changed = True
        if engine_io.LEFT.is_pressed_autorepeat:
            self.options[self.table.get_id()].decvalue(self.data)
            self.table.set_text(1,self.table.selectedrow ,self.options[self.table.get_id()].getvalue(self.data))
            if self.options[self.table.get_id()].refresh:
                self.refresh()
            
            
            self.changed = True

    def modeHelp(self):
        if engine_io.B.is_just_pressed:
            self.footerbox.mark_destroy()
            self.footertext.mark_destroy()
            self.helptextnode.mark_destroy()
            self.init()
            self.initoptions()
            #restore selection
            self.table.selectedrow = self.selectedrow
            self.table.selectedcol = self.selectedcol
            engine.tick()
            self.mode = MODE_OPTIONS
        if engine_io.DOWN.is_pressed:
              if self.helptextnode.position.y > self.helpbottom:
                  self.helptextnode.position.y -= 2
        if engine_io.UP.is_pressed:
              if self.helptextnode.position.y < self.helptop:
                  self.helptextnode.position.y += 2

    def tick(self, dt):
        if self.mode == MODE_OPTIONS:
           self.modeOptions()
        if self.mode == MODE_HELP:
           self.modeHelp()
     
     
    def show(self):
        rememberfps = engine.fps_limit()
        engine.fps_limit(60)
        
        self.initoptions()
        while True:
            if engine.tick():
                if self.quit:
                    break
    
        self.clear()
        engine.fps_limit(rememberfps)

        
