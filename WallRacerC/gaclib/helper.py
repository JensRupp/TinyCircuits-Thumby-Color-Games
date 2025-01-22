from engine_math import Vector2
from engine_resources import FontResource
from engine_nodes import Text2DNode
from math import ceil
from engine_draw import Color

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 128

class Format():
    def __init__(self, font: FontResource, scale: Vector2, color: Color):
        self.font = font
        self.scale = scale
        self.color = color

#A class that groups all settings to render a text
class Text():
    def __init__(self, text: str, font: FontResource, scale: Vector2, color: Color):
        self.text = text
        self.font = font
        self.scale = scale
        self.color = color


def align_left(node, offset = 0, parentwidth = SCREEN_WIDTH):
    node.position.x = - parentwidth // 2 + ceil((node.width * node.scale.x) /2) + offset
    
def align_right(node, offset = 0, parentwidth = SCREEN_WIDTH):
    node.position.x = parentwidth // 2 - (node.width * node.scale.x) // 2 - offset

def align_top(node, offset = 0, parentheight = SCREEN_HEIGHT):
    node.position.y = - parentheight // 2 + ceil((node.height * node.scale.y)/2) + offset

def align_bottom(node, offset = 0, parentheight = SCREEN_HEIGHT):
    node.position.y = parentheight // 2 - (node.height * node.scale.y) // 2 - offset
    

def word_wrap(text,font: FontResource, scale: Vector2, width):
  full = ""  
  lines = text.splitlines()
  for line in lines:
      buildline = ""
      words = line.split()
      first = True
      for word in words:
          if first:
              temp = word
          else:
              temp = buildline + ' ' + word
          # check length of temnp line
          tempnode = Text2DNode(Vector2(0,0),
                           font,
                           temp,
                           0,
                           scale,
                           1,
                           0,
                           0)
          if (tempnode.width < width) or first:
              #word does fit
              buildline = temp
          else:
              # word does not fit
              full = full + buildline + "\n"
              buildline = word
          tempnode.mark_destroy()              
          first = False    
      full = full +  buildline + "\n"
  return full
