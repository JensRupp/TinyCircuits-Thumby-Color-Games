from gaclib import table
from gaclib import helper
from engine_nodes import Text2DNode
from engine_math import Vector2
import engine
import engine_io
import engine_save
import json


class highscore():
    def __init__(self, showtitle: helper.Text, showsubtitle: helper.Format, showfooter: helper.text, showtable: helper.format, entertitle: helper.Text, enterfooter: helper.text, letter: helper.format, selected: Color, count: int, save: str):
        super().__init__()
        self.showtitle = showtitle
        self.showsubtitle = showsubtitle
        self.showfooter = showfooter
        self.showtable = showtable
        
        self.entertitle = entertitle
        self.enterfooter = enterfooter
        
        self.letter = letter
        self.selected = selected

        self.count = count
        self.save = save

        self.subtitle = {}
        self.loadHighscore()
        
    def register(self, id: str, subtitle: str, base: int, name:str):
        if (self.score == None):
            self.score = {}

        if not (id in self.score):
            score = []
            for index in range(0, self.count):
                score.append([(self.count - index) * base, name])
            self.score[id] = score
        if not id in self.subtitle:
            self.subtitle[id] = subtitle

    def saveHighscore(self):
        engine_save.save("highscore", json.dumps(self.score))
        engine_save.save("lasthigh", self.lasthigh)
        
    def loadHighscore(self):
        #remove comment to clear highscore on startup
        #engine_save.delete("highscore")
        engine_save.set_location(self.save)
        hs = engine_save.load("highscore", None)
        #print(hs)
        if hs != None:
            self.score = json.loads(hs)
        else:
            self.score = {}
        #print(self.score)
        
            
        self.lasthigh = engine_save.load("lasthigh", "AAA")
        


    def setcolor(self,pos,letter):
        for x in range(3):
            if x == pos:
                letter[x].color = self.selected
            else:
                letter[x].color = self.letter.color
      
      
    def setHighscore(self,id,points,name):
        
        # find the position
        score = self.score[id]
        found = -1
        for search in range(self.count-1,-1,-1):
            #print("check " + str(search)+" h=" + str(score[search][0]))
            if points <= score[search][0]:
                found = search
                break
        # Position to insert the highscore
        found = found + 1        
        # move all other one down
        if found < self.count:
            for move in range(self.count-1, found , -1):
                score[move][0] = score[move-1][0]
                score[move][1] = score[move-1][1]
            # set new score
            score[found][0] = points
            score[found][1] = name
            
            self.saveHighscore()
          
      
    def enter(self, id:str, newscore: int):
        title = Text2DNode(
                  position=Vector2(0, 0),
                  text=self.entertitle.text,
                  font=self.entertitle.font,
                  color=self.entertitle.color,
                  scale=self.entertitle.scale
                )
        helper.align_top(title)
        
        footer = Text2DNode(
                  position=Vector2(0, 0),
                  text=self.enterfooter.text,
                  font=self.enterfooter.font,
                  color=self.enterfooter.color,
                  scale=self.enterfooter.scale
                )
        helper.align_bottom(footer)
        helper.align_left(footer)
        
        pos = 0
        letter = []
    
        for p in range(3):
            highscore_letter = Text2DNode(
                position=Vector2(-66+32 + p*36, 10),
                text=self.lasthigh[p],
                font=self.letter.font,
                color=self.letter.color,
                scale=self.letter.scale,
            )
            letter.append(highscore_letter)
        self.setcolor(pos,letter)    
        
       
        
        while True:
            if engine.tick():
                if engine_io.A.is_just_pressed:
                    pos = pos + 1
                    if pos == 3:
                        break
                    self.setcolor(pos,letter)    
                if engine_io.UP.is_just_pressed:
                    n = ord(letter[pos].text[0])
                    n = n + 1
                    if n > 95:
                        n = 32
                    #print(n)
                    letter[pos].text = str(chr(n))
                if engine_io.DOWN.is_just_pressed:
                    n = ord(letter[pos].text[0])
                    n = n - 1
                    if n < 32:
                        n = 95  
                    #print(n)
                    letter[pos].text = str(chr(n))
                
                if engine_io.LEFT.is_just_pressed:
                    pos = pos - 1
                    if pos == -1:
                        pos = 2
                    self.setcolor(pos,letter)    
                if engine_io.RIGHT.is_just_pressed:
                    pos = pos + 1
                    if pos == 3:
                        pos = 0
                    self.setcolor(pos,letter)
        self.lasthigh = letter[0].text + letter[1].text + letter[2].text            
        self.setHighscore(id, newscore, self.lasthigh)

        title.mark_destroy()
        footer.mark_destroy()
        for p in range(3):
            letter[p].mark_destroy()
        

    
      
    def check(self,id: str, newscore: int):
        score = self.score[id]
        if newscore > score[self.count-1][0]:
            self.enter(id, newscore)
            return True
        return False
            
        
    def show(self, id: str):
        #print(id)
        title = Text2DNode(
            position=Vector2(0, 0),
            text=self.showtitle.text,
            font=self.showtitle.font,
            color=self.showtitle.color,
            scale=self.showtitle.scale
            )
        helper.align_top(title)
        
        score = self.score[id]
        
        subtitle = Text2DNode(
            position=Vector2(0, 0),
            text=self.subtitle[id],
            font=self.showsubtitle.font,
            color=self.showsubtitle.color,
            scale=self.showsubtitle.scale
            )
        helper.align_top(subtitle, title.height * title.scale.y +2)
        
        footer = Text2DNode(
            position=Vector2(0, 0),
            text=self.showfooter.text,
            font=self.showfooter.font,
            color=self.showfooter.color,
            scale=self.showfooter.scale
            )
        helper.align_bottom(footer)
        helper.align_left(footer)
        
        top = (title.height * title.scale.y)+2+(subtitle.height * subtitle.scale.y) 
        
        columns = [table.Column(22), table.Column(70), table.Column(128-(22+70))]
        scoretable = table.TableNode(Vector2(0,0), helper.SCREEN_WIDTH, helper.SCREEN_HEIGHT-(top + (footer.height * footer.scale.y)), self.showtable.font, self.showtable.scale, self.showtable.color, columns , 2)
        
        helper.align_top(scoretable, top)
        
        for index, row in enumerate(score):
            #print(row)
            scoretable.add_row([str(index+1)+".",str(row[0]), row[1]])
        
        while True:
            if engine.tick():
                if engine_io.A.is_just_pressed:
                    break
                if engine_io.B.is_just_pressed:
                    break
                
        scoretable.clear()
        scoretable.mark_destroy()
        title.mark_destroy()
        footer.mark_destroy()
        subtitle.mark_destroy()
        
        
