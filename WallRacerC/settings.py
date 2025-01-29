import engine_save
import json

class Settings():
    def __init__(self):
        #empty data sets defaults
        self.set({})
        
    def get(self):
        data = {}
        #these names must match the definitions in wallracer.options
        data["speed"] = self.speed
        data["link"] = self.link
        data["player1t"] = self.player1t
        data["player2t"] = self.player2t
        data["arena"] = self.arena
        data["arenasmall"] = self.arenasmall
        data["boost"] = self.boost
        data["bonus"] = self.bonus
        data["showfps"] = self.showfps
        return data
    
    def set(self, data):
        self.speed = data.get("speed", 5)
        self.link = data.get("link", False)
        self.player1t = data.get("player1t",1)
        self.player2t = data.get("player2t",1)
        self.arena = data.get("arena",3)
        self.arenasmall = data.get("arenasmall",1)
        self.boost = data.get("boost",1)
        self.bonus = data.get("bonus",1)
        self.showfps = data.get("showfps", False)
        
    def highscore_id(self):
        #highscore for now only on single player
        if (not self.link) and (self.player1t == 1):
            id = "S"+str(self.speed)+"A"+str(self.arena)+"B"+str(self.bonus)    
        else:    
            id = ""
        return id    
        
        
    def save(self):
        engine_save.set_location("wallracer.data")    
        data = self.get()
        data_json = json.dumps(data)
        engine_save.save("options", data_json)
    
    def load(self):
        engine_save.set_location("wallracer.data")
        data_json = engine_save.load("options", json.dumps(self.get()))
        data = json.loads(data_json)
        self.set(data)
