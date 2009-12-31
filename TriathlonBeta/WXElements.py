# -*- coding: iso-8859-1 -*-
import wx

try:
    from wx import glcanvas
    haveGLCanvas = True
except ImportError:
    haveGLCanvas = False
    noGL = True
    print "Will start without OpenGL, because wx.glcanvas is not available."

try:
# TODO - refactor this shit to prevent namespace pollution
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
    haveOpenGL = True
except ImportError:
    haveOpenGL = False
    noGL = True
    print "Will start without OpenGL, because PyOpenGL is not available."


class SelectionGUI(wx.Frame):
    def __init__(self,title,selection,choices):
        wx.Frame.__init__(self,None,title=title,size=(300,100))
        self.panel = wx.Panel(self, wx.ID_ANY)
        sizer = wx.FlexGridSizer(2,1,0,0)
        self.wxChoice = wx.Choice(self.panel, choices=choices)
        position = self.wxChoice.FindString(selection)
        if position == -1:
             position=0    
        self.wxChoice.SetSelection(position)    
        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)
        sizer.Add(self.wxChoice, 0, wx.ALIGN_CENTER, 5)
        self.okButton  = wx.Button(self.panel, id=-1, label='OK')
        self.okButton.Bind(wx.EVT_BUTTON, self.ok)
        sizer.AddGrowableRow(1)
        sizer.Add(self.okButton, 0, wx.ALIGN_CENTER, 5)
        self.panel.SetSizer(sizer)
        self.panel.Layout()
    def ok(self, event):
        global selected 
        selected = self.wxChoice.GetStringSelection()
        self.Close()

class SelectionApp(wx.App):
    def __init__(self,title,selection,choices, redirect = False):
        wx.App.__init__(self)
        self.mainWindow = SelectionGUI(title,selection,choices)
        self.mainWindow.Show(True)

def selection(title,selection,choices):
    global selected
    selected = selection
    selector = SelectionApp(title,selection,choices)
    selector.MainLoop()
    return selected

class GLCanvasBase(glcanvas.GLCanvas):
    def __init__(self, parent):
        glcanvas.GLCanvas.__init__(self, parent, -1,attribList=[wx.glcanvas.WX_GL_DOUBLEBUFFER])
        self.init = False
        self.size = None
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        if not self.init:
           self.InitGL()
           self.init = True
    def OnEraseBackground(self, event):
        pass
    def OnSize(self, event):
        size = self.size = self.GetClientSize()
        self.width = size.width
        self.height = size.height
        if self.GetContext():
            if self.GetParent().IsShown():
                self.SetCurrent()
                glViewport(0, 0, size.width, size.height)
        event.Skip()
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        if self.GetParent().IsShown():
            self.SetCurrent()
            self.OnDraw()
        event.Skip()

class NoGLVisualizationPanel(wx.Panel):
   def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        panelSizer = wx.FlexGridSizer(0,1,0,0)
        panelSizer.AddGrowableCol(0)
        panelSizer.AddGrowableRow(0)
        panelSizer.Add(wx.StaticText(self,label="No OpenGl :("), 0, wx.ALIGN_CENTER, 5)
        self.SetSizer(panelSizer)
        self.SetAutoLayout(1)
   def newReading(self):
        a=0
   def resetReading(self):
        a=0
   def setHistory(self, history):
        a=0

