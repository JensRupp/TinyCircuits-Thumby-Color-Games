import time

class log():
    def __init__(self, filename: str):
        self.running = False
        self.filename = filename
        self.Logfile = None
        
    def start(self):
        self.logfile = open(self.filename, "a")
        self.running = True
        
    def log(self, msg: str):
        if self.running:
            xmsg = str(time.ticks_ms()) + ": " + msg
            self.logfile.write(xmsg + "\n")
            self.logfile.flush()        
        
        
    def info(self, msg: str):
        if self.running:
            xmsg =  str(time.ticks_ms()) + ": (INFO) " + msg
            self.logfile.write(xmsg + "\n")
            self.logfile.flush()        
            
    def error(self, msg: str):
        if self.running:
            xmsg = str(time.ticks_ms()) + ": (ERROR) " + msg
            self.logfile.write(xmsg + "\n")
            self.logfile.flush()        
        
        
        