import engine_io
from engine_nodes import EmptyNode, Text2DNode, Rectangle2DNode
from engine_math import Vector2
from engine_draw import Color
from gaclib import helper


SELECTION_NONE = 0
SELECTION_ROW = 1
SELECTION_NODE = 2 # not implemented

class Column():
    def __init__(self, width: float):
        self.width = width
                

class TableNode(EmptyNode):
    def __init__(self, position: Vector2, width: float, height: float, font: FontResource, scale: Vector2, color: Color, columns, layer):
        super().__init__(self)
        self.position.x = position.x
        self.position.y = position.y
        self.outline= True
        self.width = width
        self.height = height
        self.columns = columns
        self.font = font
        self.scale = scale
        self.color = color
        self.selcolor = color
        self.layer = layer
        self.rows = []
        self.id = []
        self.top = 0
        self.left = 0
        self.selection = SELECTION_NONE
        self.selectedrow = 0
        self.selectedcol = 0
        self.callback = None
        self.rowheight = (self.font.height * self.scale.y) + 1
        self.rowcount = (self.height+1) // self.rowheight
        #print("height: "+str(self.height)+" rowheight="+str(self.rowheight)+" rowcount="+str(self.rowcount))
        self.changed = True
        
    def add_row(self, row, id = 0):
        nodes = []
        
        for col in row:
            text = Text2DNode(Vector2(0,0),
                           self.font,
                           col,
                           0,
                           self.scale,
                           1,
                           1,
                           1,
                           self.color,
                           self.layer)
            self.add_child(text)
            #print("Test")
            #print(text)
            #print(type(text.get_parent)) 
            #print(callable(text.get_parent()))
            
            nodes.append(text)
        self.rows.append(nodes)
        self.id.append(id)
        self.changed = True
             
    
    def clear(self):
        self.mark_destroy_children()
        self.rows = []
        self.id = []
        self.changed = True
                
    def get_node(self, x: int,y: int):
        return self.rows[y][x]
    
    def set_text(self, x: int, y: int, text: str):
        node = self.get_node(x,y)
        if node.text != text:
            node.text = text
            self.changed = True
            
    def get_id(self):
        return self.id[self.selectedrow]
    
    def set_color(self, x: int, y: int, color: Color):
        node = self.get_node(x,y)
        node.color = color
        
    def update(self):
        if self.changed:
            #print("rowcount="+str(self.rowcount))
            #print("selfy="+str(self.position.y))
            #print("selfx="+str(self.position.x))
            
            currenty = 0 #self.position.y
            for rowindex, row in enumerate(self.rows):
                currentx = 0 #self.position.x
                #print("row="+str(rowindex))
                if (rowindex >= self.top) and (rowindex < self.top + self.rowcount):
                    for colindex, col in enumerate(row):
                        #print("col="+str(colindex)) and ((currentx + self.columns[colindex].width) <= self.width)
                        if (colindex  >= self.left):
                            col.opacity = 1
                            #print("col="+str(colindex)+" row="+str(rowindex)+" x="+str(currentx)+" y="+str(currenty))
                            helper.align_left(col, currentx, self.width)
                            helper.align_top(col, currenty, self.height)
                            
                            if self.selection == SELECTION_ROW:
                                #print("SELECTION_ROW "+str(rowindex)+" "+str(self.selectedrow))
                                if rowindex == self.selectedrow:
                                    col.color = self.selcolor
                                else:    
                                    col.color = self.color
                            elif self.selection == SELECTION_NODE:
                                if (rowindex == self.selectedrow) and (colindex == self.selectedcol):
                                    col.color = self.selcolor
                                else:    
                                    col.color = self.color
                            else:
                                col.color = self.color
                            currentx += self.columns[colindex].width
                        else:
                            #hide not visible col
                            col.opacity = 0
                    currenty += self.rowheight     
                else:
                    #hide full not visible row
                    for col in row:
                        col.opacity = 0
            self.changed = False
            if self.callback != None:
                self.callback()
    
    def tick(self, dt):
        if (self.selection == SELECTION_ROW) or (self.selection == SELECTION_NODE):
            if engine_io.DOWN.is_pressed_autorepeat:
                if self.selectedrow < len(self.rows)-1:
                    self.selectedrow += 1
                    if self.selectedrow - self.top >= self.rowcount:
                        self.top += 1
                    self.changed = True
            if engine_io.UP.is_pressed_autorepeat:
                if self.selectedrow > 0:
                    self.selectedrow -= 1
                    if self.selectedrow < self.top:
                        self.top = self.selectedrow
                    self.changed = True
        else:
            if engine_io.DOWN.is_pressed_autorepeat:
                if self.top+self.rowcount < len(self.rows):
                    self.top += 1
                    self.changed = True
            if engine_io.UP.is_pressed_autorepeat:
                if self.top > 0:
                    self.top -= 1
                    self.changed = True
            
        self.update()    
                    
                    
                
        

     
