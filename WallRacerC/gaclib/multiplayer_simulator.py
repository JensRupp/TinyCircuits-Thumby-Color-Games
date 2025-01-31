from engine_nodes import EmptyNode
from gaclib import multiplayer

VALUE_BYTE = 0  # 1 byte
VALUE_WORD = 1  # 2 byte
VALUE_DWORD= 2  # 4 byte


class MultiplayerNodeSimulator(EmptyNode):
    def __init__(self):
       super().__init__(self) 
    
    def write_byte(self, pos: int ,value: int):
        v = int(value)
        self.buffer[pos] = v & 0b11111111

    def write_byte_player(self, pos: int ,value: int, player: int):
        v = int(value)
        self.buffer[pos+player] = v & 0b11111111
       
    def write_word(self, pos: int,value: int):
        v = int(value)
        self.buffer[pos] = v & 0b11111111
        self.buffer[pos+1] = (v >> 8)  & 0b11111111

    def write_word_player(self, pos: int,value: int, player: int):
        v = int(value)
        pos += 2*player
        self.buffer[pos] = v & 0b11111111
        self.buffer[pos+1] = (v >> 8)  & 0b11111111

    def write_dword(self, pos: int,value: int):
        v = int(value)
        self.buffer[pos] = v & 0b11111111
        self.buffer[pos+1] = (v >> 8)  & 0b11111111
        self.buffer[pos+2] = (v >> 16)  & 0b11111111
        self.buffer[pos+3] = (v >> 24)  & 0b11111111

    def write_dword_player(self, pos: int,value: int, player: int):
        v = int(value)
        pos += 4*player
        self.buffer[pos] = v & 0b11111111
        self.buffer[pos+1] = (v >> 8)  & 0b11111111
        self.buffer[pos+2] = (v >> 16)  & 0b11111111
        self.buffer[pos+3] = (v >> 24)  & 0b11111111
       
    def write(self, name, value: int):
        v = self.values[name]
        if v.type == VALUE_BYTE:
            self.write_byte(v.pos, value)
        elif v.type == VALUE_WORD:
            self.write_word(v.pos, value)
        elif v.type == VALUE_DWORD:
            self.write_dword(v.pos, value)            

 
    def write_player(self, name, value: int, player: int):
        v = self.values[name]
        if v.type == VALUE_BYTE:
            self.write_byte_player(v.pos, value, player)
        elif v.type == VALUE_WORD:
            self.write_word_player(v.pos, value, player)
        elif v.type == VALUE_DWORD:
            self.write_dword_player(v.pos, value, player)            
        

    def read_byte(self, pos: int) -> int:
        return self.buffer[pos]
        
    def read_byte_player(self, pos: int, player: int) -> int:
        return self.buffer[pos + player]

    def read_word(self, pos: int) -> int:
        v = self.buffer[pos] + (self.buffer[pos+1] << 8 )
        return v
        

    def read_word_player(self, pos: int, player: int) -> int:
        pos += 2*player
        v = self.buffer[pos] + (self.buffer[pos+1] << 8 )
        return v


    def read_dword(self, pos: int) -> int:
        v = self.buffer[pos] + (self.buffer[pos+1] << 8 ) + (self.buffer[pos+2] << 16 ) + + (self.buffer[pos+3] << 24 )
        return v

    def read_dword_player(self, pos: int, player: int) -> int:
        pos += 4*player
        v = self.buffer[pos] + (self.buffer[pos+1] << 8 ) + (self.buffer[pos+2] << 16 ) + + (self.buffer[pos+3] << 24 )
        return v

    def read(self, name) -> int:
        v = self.values[name]
        if v.type == VALUE_BYTE:
            return self.read_byte(v.pos)
        elif v.type == VALUE_WORD:
            return self.read_word(v.pos)
        elif v.type == VALUE_DWORD:
            return self.read_dword(v.pos)
        
    def read_player(self, name, player: int) -> int:
        v = self.values[name]
        if v.type == VALUE_BYTE:
            return self.read_byte_player(v.pos,player)
        elif v.type == VALUE_WORD:
            return self.read_word_player(v.pos,player)
        elif v.type == VALUE_DWORD:
            return self.read_dword_player(v.pos,player)
        
