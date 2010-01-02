# -*- coding: iso-8859-1 -*-
try:
    import Xlib.display
    import Xlib.X        
    import Xlib.XK
    import Xlib.error
    import Xlib.ext.xtest
    haveXlib = True
except ImportError:
    haveXlib = False

try:
# TODO - refactor this shit to prevent namespace pollution
    from ctypes import *
    import win32con
    haveWindows = True
except ImportError:
    haveWindows = False

class Action():
    def __init__(self,xLibKeyCode=-1,win32KeyCode=-1,shiftDown=False,controlDown=False,altDown=False,extend=False,mouseButton=False,mouseMovement=False):
        self.xLibKeyCode = xLibKeyCode
        self.win32KeyCode = win32KeyCode
        self.shiftDown = shiftDown
        self.controlDown = controlDown
        self.altDown = altDown
        self.extend = extend
        self.mouseButton = mouseButton
        self.mouseMovement = mouseMovement
        self.isDown = False

actions = {} 

if haveWindows:
    user32 = windll.user32
    PUL = POINTER(c_ulong)
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_SCANCODE = 0x0008
    
    MOUSEEVENTF_LEFTDOWN   = 0x0002
    MOUSEEVENTF_LEFTUP     = 0x0004
    MOUSEEVENTF_RIGHTDOWN  = 0x0008
    MOUSEEVENTF_RIGHTUP    = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP   = 0x0040
    MOUSEEVENTF_RELATIVE   = 0x0000
    MOUSEEVENTF_MOVE       = 0x0001
    MOUSEEVENTF_ABSOLUTE   = 0x8000
    MOUSEEVENTF_WHEEL      = 0x0080
    MOUSEEVENTF_XDOWN      = 0x0100
    MOUSEEVENTF_XUP        = 0x0200
    INPUT_MOUSE = 0x0000
    INPUT_KEYBOARD = 0x0001
    INPUT_HARDWARE = 0x0002    

    class KeyBdInput(Structure):
        _fields_ = [("wVk", c_ushort),
                 ("wScan", c_ushort),
                 ("dwFlags", c_ulong),
                 ("time", c_ulong),
                 ("dwExtraInfo", PUL)]
    
    class HardwareInput(Structure):
        _fields_ = [("uMsg", c_ulong),
                 ("wParamL", c_short),
                 ("wParamH", c_ushort)]
    
    class MouseInput(Structure):
        _fields_ = [("dx", c_long),
                 ("dy", c_long),
                 ("mouseData", c_ulong),
                 ("dwFlags", c_ulong),
                 ("time",c_ulong),
                 ("dwExtraInfo", PUL)]
    
    class Input_I(Union):
        _fields_ = [("ki", KeyBdInput),
                  ("mi", MouseInput),
                  ("hi", HardwareInput)]
    
    class Input(Structure):
        _fields_ = [("type", c_ulong),
                 ("ii", Input_I)]
    
    class POINT(Structure):
        _fields_ = [("x", c_ulong),
                 ("y", c_ulong)]

    nums  = "0123456789"
    chars = "abcdefghijklmnopqrstuvwxyz"
    for i in range(len(nums)):
        actions[nums[i]] = Action(win32KeyCode = 0x30 + i)
    for i in range(len(chars)):
        actions[chars[i]] = Action(win32KeyCode = 0x41 + i )
    actions["Arrow Left"] = Action(win32KeyCode = 0x25,extend=True )
    actions["Arrow Right"] = Action(win32KeyCode = 0x27,extend=True )
    actions["Arrow Up"] = Action(win32KeyCode = 0x26,extend=True )
    actions["Arrow Down"] = Action(win32KeyCode = 0x28,extend=True )
    actions["F1"] = Action(win32KeyCode = 0x70,extend=True )
    actions["F2"] = Action(win32KeyCode = 0x71,extend=True )
    actions["F3"] = Action(win32KeyCode = 0x72,extend=True )
    actions["F4"] = Action(win32KeyCode = 0x73,extend=True )
    actions["F5"] = Action(win32KeyCode = 0x74,extend=True )
    actions["F6"] = Action(win32KeyCode = 0x75,extend=True )
    actions["F7"] = Action(win32KeyCode = 0x76,extend=True )
    actions["F8"] = Action(win32KeyCode = 0x77,extend=True )
    actions["F9"] = Action(win32KeyCode = 0x78,extend=True )
    actions["F10"] = Action(win32KeyCode = 0x79,extend=True )
    actions["F11"] = Action(win32KeyCode = 0x7a,extend=True )
    actions["F12"] = Action(win32KeyCode = 0x7b,extend=True )
    actions["Enter"] = Action(win32KeyCode = 0x0d,extend=True )
    actions["Space"] = Action(win32KeyCode = 0x20,extend=True )
    actions["Backspace"] = Action(win32KeyCode = 0x08,extend=True )
    actions["Page Up"] = Action(win32KeyCode = 0x21,extend=True )
    actions["Page Down"] = Action(win32KeyCode = 0x22,extend=True )
    actions["Home"] = Action(win32KeyCode = 0x24,extend=True )
    actions["End"] = Action(win32KeyCode = 0x23,extend=True )
    actions["Insert"] = Action(win32KeyCode = 0x2d,extend=True )
    actions["Delete"] = Action(win32KeyCode = 0x2e,extend=True )
    actions["Mouse Button Left"] = Action(win32KeyCode = 0x1,mouseButton=True )
    actions["Mouse Button Right"] = Action(win32KeyCode = 0x2,mouseButton=True )
    actions["Mouse Button Middle"] = Action(win32KeyCode = 0x3,mouseButton=True )
    actions["Mouse Move Slow Left"] = Action(win32KeyCode = (-5,0),mouseMovement=True)
    actions["Mouse Move Slow Right"] = Action(win32KeyCode = (5,0),mouseMovement=True)
    actions["Mouse Move Slow Up"] = Action(win32KeyCode = (0,-5),mouseMovement=True)
    actions["Mouse Move Slow Down"] = Action(win32KeyCode = (0,5),mouseMovement=True)
    actions["Mouse Move Fast Left"] = Action(win32KeyCode = (-50,0),mouseMovement=True)
    actions["Mouse Move Fast Right"] = Action(win32KeyCode = (50,0),mouseMovement=True)
    actions["Mouse Move Fast Up"] = Action(win32KeyCode = (0,-50),mouseMovement=True)
    actions["Mouse Move Fast Down"] = Action(win32KeyCode = (0,50),mouseMovement=True) 

if haveXlib:
    display = Xlib.display.Display()
    for each in "1234567890abcdefghijklmnopqrstuvwxyz":
        actions[each] = Action(xLibKeyCode= display.keysym_to_keycode(ord(each)))
        #actions[each.upper()] = Action(xLibKeyCode= display.keysym_to_keycode(each),shiftDown=True)
        #actions["Ctrl "+each] = Action(xLibKeyCode= display.keysym_to_keycode(each),controlDown=True)
        #actions["Ctrl "+each.upper()] = Action(xLibKeyCode= display.keysym_to_keycode(each),shiftDown=True,controlDown=True)
        #actions["Alt "+each] = Action(xLibKeyCode= display.keysym_to_keycode(each),altDown=True)
        #actions["Alt "+each.upper()] = Action(xLibKeyCode= display.keysym_to_keycode(each),shiftDown=True,altDown=True)
        #actions["Ctrl Alt "+each] = Action(xLibKeyCode= display.keysym_to_keycode(each),controlDown=True,altDown=True)
        #actions["Ctrl Alt "+each.upper()] = Action(xLibKeyCode= display.keysym_to_keycode(each),shiftDown=True,controlDown=True,altDown=True)
    actions["Arrow Left"] = Action(xLibKeyCode=113)
    actions["Arrow Right"] = Action(xLibKeyCode=114)
    actions["Arrow Up"] = Action(xLibKeyCode=111)
    actions["Arrow Down"] = Action(xLibKeyCode=116)
    actions["F1"] = Action(xLibKeyCode=67)
    actions["F2"] = Action(xLibKeyCode=68)
    actions["F3"] = Action(xLibKeyCode=69)
    actions["F4"] = Action(xLibKeyCode=70)
    actions["F5"] = Action(xLibKeyCode=71)
    actions["F6"] = Action(xLibKeyCode=72)
    actions["F7"] = Action(xLibKeyCode=73)
    actions["F8"] = Action(xLibKeyCode=74)
    actions["F9"] = Action(xLibKeyCode=75)
    actions["F10"] = Action(xLibKeyCode=76)
    actions["F11"] = Action(xLibKeyCode=95)
    actions["F12"] = Action(xLibKeyCode=96)
    actions["Enter"] = Action(xLibKeyCode=36)
    actions["Space"] = Action(xLibKeyCode=65)
    actions["Backspace"] = Action(xLibKeyCode=22)
    actions["Page Up"] = Action(xLibKeyCode=112)
    actions["Page Down"] = Action(xLibKeyCode=117)
    actions["Home"] = Action(xLibKeyCode=110)
    actions["End"] = Action(xLibKeyCode=115)
    actions["Insert"] = Action(xLibKeyCode=118)
    actions["Delete"] = Action(xLibKeyCode=119)
    actions["Mouse Button Left"] = Action(xLibKeyCode = 1,mouseButton=True )
    actions["Mouse Button Right"] = Action(xLibKeyCode = 3,mouseButton=True )
    actions["Mouse Button Middle"] = Action(xLibKeyCode = 2,mouseButton=True )
    actions["Mouse Move Slow Left"] = Action(xLibKeyCode = (-5,0),mouseMovement=True)
    actions["Mouse Move Slow Right"] = Action(xLibKeyCode = (5,0),mouseMovement=True)
    actions["Mouse Move Slow Up"] = Action(xLibKeyCode = (0,-5),mouseMovement=True)
    actions["Mouse Move Slow Down"] = Action(xLibKeyCode = (0,5),mouseMovement=True)
    actions["Mouse Move Fast Left"] = Action(xLibKeyCode = (-50,0),mouseMovement=True)
    actions["Mouse Move Fast Right"] = Action(xLibKeyCode = (50,0),mouseMovement=True)
    actions["Mouse Move Fast Up"] = Action(xLibKeyCode = (0,-50),mouseMovement=True)
    actions["Mouse Move Fast Down"] = Action(xLibKeyCode = (0,50),mouseMovement=True) 

class XLibInputFaker():
    def __init__(self):
        self.actions = actions
        InputFaker.__init__(self)
        self.display = Xlib.display.Display()
    def keyHold(self,key):
        if not(self.actions[key].isDown):
            if self.actions[key].mouseButton: 
                self.mouseButtonHold(self.actions[key].xLibKeyCode)
                self.actions[key].isDown = True
            elif self.actions[key].mouseMovement: 
                self.mouseMove(self.actions[key].xLibKeyCode[0],self.actions[key].xLibKeyCode[1])
            else:
                if self.actions[key].shiftDown:
                    Xlib.ext.xtest.fake_input(self.display,Xlib.X.KeyPress, 50)
                if self.actions[key].controlDown:
                    Xlib.ext.xtest.fake_input(self.display,Xlib.X.KeyPress, 37)
                if self.actions[key].altDown:
                    Xlib.ext.xtest.fake_input(self.display,Xlib.X.KeyPress, 64)
                Xlib.ext.xtest.fake_input(self.display,Xlib.X.KeyPress, self.actions[key].xLibKeyCode)
                self.actions[key].isDown = True
    def keyRelease(self,key):
        if (self.actions[key].isDown):
            if self.actions[key].mouseButton:
                self.mouseButtonRelease(self.actions[key].xLibKeyCode)
                self.actions[key].isDown = False
            elif not(self.actions[key].mouseMovement):
                if self.actions[key].shiftDown:
                     Xlib.ext.xtest.fake_input(self.display,Xlib.X.KeyRelease, 50)
                if self.actions[key].controlDown:
                     Xlib.ext.xtest.fake_input(self.display,Xlib.X.KeyRelease, 37)
                if self.actions[key].altDown:
                    Xlib.ext.xtest.fake_input(self.display,Xlib.X.KeyRelease, 64)
                Xlib.ext.xtest.fake_input(self.display,Xlib.X.KeyRelease, self.actions[key].xLibKeyCode)
                self.actions[key].isDown = False
    def keyPress(self,key):
        self.keyHold(key)
        self.keyRelease(key)
    def mouseMove(self,x,y):
        Xlib.ext.xtest.fake_input(self.display,Xlib.X.MotionNotify,True,x=x,y=y)
    def mouseButtonHold(self,buttonNumber):
        Xlib.ext.xtest.fake_input(self.display,Xlib.X.ButtonPress, buttonNumber)
    def mouseButtonRelease(self,buttonNumber):
        Xlib.ext.xtest.fake_input(self.display,Xlib.X.ButtonRelease, buttonNumber)
    def mouseButtonPress(self,buttonNumber):
        self.mouseButtonHold(buttonNumber)
        self.mouseButtonRelease(buttonNumber)
    def flush(self):
        self.display.sync()

class WindowsInputFaker():
    def __init__(self):
        self.actions = actions
        InputFaker.__init__(self)
        self.inputItem = {}
        self.inputItem["mouse"] = []
        self.inputItem["keyboard"] = []
    def keyHold(self,key):
        if not(self.actions[key].isDown):
            if self.actions[key].mouseButton:
                self.mouseButtonHold(self.actions[key].win32KeyCode)
                self.actions[key].isDown = True
            elif self.actions[key].mouseMovement:
                self.mouseMove(self.actions[key].win32KeyCode[0],self.actions[key].win32KeyCode[1])
            else:             
                if self.actions[key].shiftDown:
                    extra = c_ulong(0)
                    self.inputItem["keyboard"].append(Input_I())
                    self.inputItem["keyboard"][-1].ki = KeyBdInput(0, user32.MapVirtualKeyA(win32con.VK_SHIFT, 0), KEYEVENTF_SCANCODE, 0, pointer(extra))
                if self.actions[key].controlDown:
                    extra = c_ulong(0)
                    self.inputItem["keyboard"].append(Input_I())
                    self.inputItem["keyboard"][-1].ki = KeyBdInput(0, user32.MapVirtualKeyA(win32con.VK_CONTROL, 0), KEYEVENTF_SCANCODE, 0, pointer(extra))
                if self.actions[key].altDown:
                    extra = c_ulong(0)
                    self.inputItem["keyboard"].append(Input_I())
                    self.inputItem["keyboard"][-1].ki = KeyBdInput(0, user32.MapVirtualKeyA(win32con.VK_ALT, 0), KEYEVENTF_SCANCODE, 0, pointer(extra))
                if self.actions[key].extend == True:
                    extra = c_ulong(0)
                    self.inputItem["keyboard"].append(Input_I())
                    self.inputItem["keyboard"][-1].ki = KeyBdInput(0, user32.MapVirtualKeyA(self.actions[key].win32KeyCode, 0), KEYEVENTF_EXTENDEDKEY, 0, pointer(extra))
                else:
                    extra = c_ulong(0)
                    self.inputItem["keyboard"].append(Input_I())
                    self.inputItem["keyboard"][-1].ki = KeyBdInput(0, user32.MapVirtualKeyA(self.actions[key].win32KeyCode, 0), KEYEVENTF_SCANCODE, 0, pointer(extra))
                self.actions[key].isDown = True
    def keyRelease(self,key):
        if (self.actions[key].isDown):
            if self.actions[key].mouseButton:
                self.mouseButtonRelease(self.actions[key].win32KeyCode)
                self.actions[key].isDown = False
            elif not(self.actions[key].mouseMovement):
                if self.actions[key].extend == True:
                    extra = c_ulong(0)
                    self.inputItem["keyboard"].append(Input_I())
                    self.inputItem["keyboard"][-1].ki = KeyBdInput(0, user32.MapVirtualKeyA(self.actions[key].win32KeyCode, 0), KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0, pointer(extra))
                else:
                    extra = c_ulong(0)
                    self.inputItem["keyboard"].append(Input_I())
                    self.inputItem["keyboard"][-1].ki = KeyBdInput(0, user32.MapVirtualKeyA(self.actions[key].win32KeyCode, 0), KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, pointer(extra))
                if self.actions[key].altDown:
                    extra = c_ulong(0)
                    self.inputItem["keyboard"].append(Input_I())
                    self.inputItem["keyboard"][-1].ki = KeyBdInput(0, user32.MapVirtualKeyA(win32con.VK_ALT, 0), KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, pointer(extra))
                if self.actions[key].controlDown:
                    extra = c_ulong(0)
                    self.inputItem["keyboard"].append(Input_I())
                    self.inputItem["keyboard"][-1].ki = KeyBdInput(0, user32.MapVirtualKeyA(win32con.VK_CONTROL, 0), KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, pointer(extra))
                if self.actions[key].shiftDown:
                    extra = c_ulong(0)
                    self.inputItem["keyboard"].append(Input_I())
                    self.inputItem["keyboard"][-1].ki = KeyBdInput(0, user32.MapVirtualKeyA(win32con.VK_SHIFT, 0), KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, pointer(extra))
                self.actions[key].isDown = False
    def keyPress(self,key):
        self.keyHold(key)
        self.keyRelease(key)
    def mouseMove(self,x,y):
        extra = c_ulong(0)
        self.inputItem["mouse"].append(Input_I())
        self.inputItem["mouse"][-1].mi = MouseInput(x, y, 0, MOUSEEVENTF_MOVE, 0, pointer(extra))
    def mouseButtonHold(self,buttonNumber):
        if buttonNumber == 1:
            mouseButton = MOUSEEVENTF_LEFTDOWN
        elif buttonNumber == 2:
            mouseButton = MOUSEEVENTF_RIGHTDOWN
        elif buttonNumber == 3:
            mouseButton = MOUSEEVENTF_MIDDLEDOWN
        extra = c_ulong(0)
        self.inputItem["mouse"].append(Input_I())
        self.inputItem["mouse"][-1].mi = MouseInput(0, 0, 0, mouseButton, 0, pointer(extra))
    def mouseButtonRelease(self,buttonNumber):
        if buttonNumber == 1:
            mouseButton = MOUSEEVENTF_LEFTUP
        elif buttonNumber == 2:
            mouseButton = MOUSEEVENTF_RIGHTUP
        elif buttonNumber == 3:
            mouseButton = MOUSEEVENTF_MIDDLEUP
        extra = c_ulong(0)
        self.inputItem["mouse"].append(Input_I())
        self.inputItem["mouse"][-1].mi = MouseInput(0, 0, 0, mouseButton, 0, pointer(extra))
    def mouseButtonPress(self,buttonNumber):
        self.mouseButtonHold(buttonNumber)
        self.mouseButtonRelease(buttonNumber)
    def flush(self):
        numItems = len(self.inputItem["mouse"]) + len(self.inputItem["keyboard"])
        if numItems > 0:
            FInputs = Input * numItems
            x = FInputs()
            counter = 0
            for mouse in self.inputItem["mouse"]:
                x[counter].type = INPUT_MOUSE
                x[counter].ii = mouse
                counter = counter + 1
            for keyboard in self.inputItem["keyboard"]:
                x[counter].type = INPUT_KEYBOARD
                x[counter].ii = keyboard
                counter = counter + 1
            user32.SendInput(numItems, pointer(x), sizeof(x[0]))
        self.inputItem["mouse"] = []
        self.inputItem["keyboard"] = []

def InputFaker():
    if haveXlib:
        faker = XLibInputFaker()
        return faker
    elif haveWindows:
        faker = WindowsInputFaker()
        return faker
    else:
        return -1

if __name__ == "__main__":
    import time
    inputFaker = InputFaker()
    if inputFaker != -1:
        time.sleep(1)
        inputFaker.mouseMove(50,50)
        inputFaker.flush()
        time.sleep(1)
        inputFaker.mouseMove(-50,-50)
        inputFaker.flush()
        time.sleep(1)
        inputFaker.mouseMove(50,50)
        inputFaker.flush()
        inputFaker.keyPress('w')
        inputFaker.keyPress('a')
        inputFaker.keyPress('s')
        inputFaker.keyPress('d')
        inputFaker.flush()
    else:
        print "Error: neither XLib nor win32 could be found"
