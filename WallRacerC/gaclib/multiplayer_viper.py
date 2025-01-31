from engine_nodes import EmptyNode
from gaclib import multiplayer

VALUE_BYTE = 0  # 1 byte
VALUE_WORD = 1  # 2 byte
VALUE_DWORD= 2  # 4 byte


class MultiplayerNodeViper(EmptyNode):
    def __init__(self):
       super().__init__(self) 
    
    @micropython.viper    
    def write_byte(self, pos: int ,value: int):
        buf = ptr8(int(ptr8(self.buffer))+pos)
        buf[0] = value

    @micropython.viper    
    def write_byte_player(self, pos: int ,value: int, player: int):
        buf = ptr8(int(ptr8(self.buffer))+pos)
        buf[player] = value
       
    @micropython.viper    
    def write_word(self, pos: int,value: int):
        buf = ptr16(int(ptr8(self.buffer))+pos)
        buf[0] = value

    @micropython.viper    
    def write_word_player(self, pos: int,value: int, player: int):
        buf = ptr16(int(ptr8(self.buffer))+pos)
        buf[player] = value

        
    @micropython.viper    
    def write_dword(self, pos: int,value: int):
        buf = ptr32(int(ptr8(self.buffer))+pos)
        buf[0] = value

    @micropython.viper    
    def write_dword_player(self, pos: int,value: int, player: int):
        buf = ptr32(int(ptr8(self.buffer))+pos)
        buf[player] = value
       

    @micropython.viper            
    def write(self, name, value: int):
        v = self.values[name]
        b = int(ptr8(self.buffer)) + int(v.pos)
        if v.type == VALUE_BYTE:
            ptr8(b)[0] = value
        elif v.type == VALUE_WORD:
            ptr16(b)[0] = value
            self.write_word(v.pos, value)
        elif v.type == VALUE_DWORD:
            ptr32(b)[0] = value

            
    @micropython.viper            
    def write_player(self, name, value: int, player: int):
        v = self.values[name]
        b = int(ptr8(self.buffer)) + int(v.pos)
        if v.type == VALUE_BYTE:
            ptr8(b)[player] = value
        elif v.type == VALUE_WORD:
            ptr16(b)[player] = value
        elif v.type == VALUE_DWORD:
            ptr32(b)[player] = value

    @micropython.viper
    def read_byte(self, pos: int) -> int:
        buf = ptr8(int(ptr8(self.buffer))+pos)
        return buf[0]

    @micropython.viper
    def read_byte_player(self, pos: int, player: int) -> int:
        buf = ptr8(int(ptr8(self.buffer))+pos)
        return buf[player]

    @micropython.viper
    def read_word(self, pos: int) -> int:
        buf = ptr16(int(ptr8(self.buffer))+pos)
        return buf[0]

    @micropython.viper
    def read_word_player(self, pos: int, player: int) -> int:
        buf = ptr16(int(ptr8(self.buffer))+pos)
        return buf[player]


    @micropython.viper
    def read_dword(self, pos: int) -> int:
        buf = ptr32(int(ptr8(self.buffer))+pos)
        return buf[0]

    @micropython.viper
    def read_dword_player(self, pos: int, player: int) -> int:
        buf = ptr32(int(ptr8(self.buffer))+pos)
        return buf[int(player)]

    @micropython.viper            
    def read(self, name) -> int:
        v = self.values[name]
        b = int(ptr8(self.buffer)) + int(v.pos)
        if v.type == VALUE_BYTE:
            return ptr8(b)[0]
        elif v.type == VALUE_WORD:
            return ptr16(b)[0]
        elif v.type == VALUE_DWORD:
            return ptr32(b)[0]
        
    @micropython.viper            
    def read_player(self, name, player: int) -> int:
        v = self.values[name]
        b = int(ptr8(self.buffer)) + int(v.pos)
        if v.type == VALUE_BYTE:
            return ptr8(b)[player]
        elif v.type == VALUE_WORD:
            return ptr16(b)[player]
        elif v.type == VALUE_DWORD:
            return ptr32(b)[player]
