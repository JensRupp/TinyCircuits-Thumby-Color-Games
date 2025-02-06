import engine
import engine_io

from engine_nodes import EmptyNode, Text2DNode
from engine_math import Vector2,Vector3,
from engine_animation import Tween,  ONE_SHOT, EASE_LINEAR, EASE_QUAD_IN_OUT

from gaclib import helper
from gaclib import table

class MenuFormat():
    def __init__(self, font: FontResource, scale: Vector2, color: Color, selected: Color):
        self.font = font
        self.scale = scale
        self.color = color
        self.selected = selected

class Menu():
    def __init__(self, name, id, submenu):
        super().__init__()
        self.name = name
        self.id = id
        self.submenu = submenu
        
        self.selection = 0
        self.stack = []
        
        self.table = None


class MenuNode(EmptyNode):
    def __init__(self,  position, width, height, help: helper.Text, info: helper.Text, menuformat: OptionsFormat, menuitems):
        super().__init__(self)
        self.position = position
        self.width = width
        self.height = height
        self.scale = Vector2(1,1)
        
        self.help = help
        self.info = info
        self.menuformat = menuformat
        
        self.root = Menu("root", 0, menuitems)

        self.tween1 = Tween()
        self.tween2 = Tween()


        self.selection = 0                
        self.init()
        
       
    def init_menu(self, menuitem):
        print("menu: "+menuitem.name)
        columns = [table.Column(self.width-16), table.Column(16)]
        menuitem.table = table.TableNode(Vector2(0,0), self.width, self.height-self.helpnode.height, self.menuformat.font, self.menuformat.scale, self.menuformat.color, columns, 10)
        menuitem.table.selcolor = self.menuformat.selected
        menuitem.table.selection = table.SELECTION_ROW
        menuitem.table.position.x = 1000  # hide
        menuitem.table.active = False
        self.add_child(menuitem.table)
        
        helper.align_top(menuitem.table,0,self.height)
        print("height="+str(self.height))
        print("top="+str(menuitem.table.position.y))
        for item in menuitem.submenu:
            if item.submenu != None:
                arrow = ">"
            else:    
                arrow = ""
            print("add: "+ item.name)    
            menuitem.table.add_row([item.name,arrow], item.id)
            if item.submenu != None:
                self.init_menu(item)
        

    
    def init(self):
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
        helper.align_left(self.helpnode,0, self.width)
        helper.align_bottom(self.helpnode, 0, self.height)
        #self.listbottom = self.helpnode.position.y - self.helpnode.height // 2  
        self.add_child(self.helpnode)
        
        self.init_menu(self.root)
        self.stack = [self.root]
        # show root
        helper.align_left(self.root.table,0,self.width)
        self.root.table.active = True
    
    def tick(self, dt):
        if engine_io.B.is_just_pressed:
            if len(self.stack) == 1:
                self.selection = -1
            else:
                current_table = self.stack[-1].table
                pos_screen = current_table.position
                pos_left = Vector3(pos_screen.x - self.width, current_table.position.y,10)
                pos_right = Vector3(pos_screen.x + self.width,current_table.position.y,10)
                
                prev_table = self.stack[-2].table
                current_table.active = False
                prev_table.active = True
                
                self.tween1.start(current_table, "position", pos_screen, pos_right, 200, 1.0,  ONE_SHOT,  EASE_QUAD_IN_OUT)
                self.tween2.start(prev_table, "position", pos_left, pos_screen, 200, 1.0,  ONE_SHOT,  EASE_QUAD_IN_OUT)
                self.stack.pop()
                
        if engine_io.A.is_just_pressed:
            current_table = self.stack[-1].table
            pos_screen = current_table.position
            pos_left = Vector3(pos_screen.x - self.width, current_table.position.y,10)
            pos_right = Vector3(pos_screen.x + self.width,current_table.position.y,10)
            
            current_row = current_table.selectedrow
            current_menu = self.stack[-1].submenu[current_row]

            if current_menu.submenu == None:
                self.selection = current_menu.id
            else:
                #go to submenu
                current_table.active = False
                current_menu.table.active= True
                
                self.tween1.start(current_table, "position", pos_screen, pos_left, 200, 1.0,  ONE_SHOT,  EASE_QUAD_IN_OUT)
                self.tween2.start(current_menu.table, "position", pos_right, pos_screen, 200, 1.0,  ONE_SHOT,  EASE_QUAD_IN_OUT)
                self.stack.append(current_menu)
            
            
        
    
    def show(self):
        rememberfps = engine.fps_limit()
        engine.fps_limit(60)
        
        self.selection = 0
        self.stack = [self.root]


        while self.selection == 0:
            if engine.tick():
                pass

        engine.fps_limit(rememberfps)
        
        return self.selection

    
        