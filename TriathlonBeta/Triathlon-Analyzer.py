#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

# Howto, Code license, Credits, etc: http://code.google.com/B/BCI-Project-Triathlon/

noGL = False   # Set noGL to True for disabling the use of OpenGL (to gain speed, or to avoid python-wx-opengl problems)

import numpy
import wx
import math
import threading
import random
import sys
import os
import random

import InputManager
import WXElements

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

class AppSettings():
    def __init__(self,
                 niaFPS           = 10,
                 deviceName       = "OCZ Neural Impulse Actuator",
                 bands            = [(2,4),(5,7),(8,10),(11,13),(14,16),(17,20),(21,24),(25,30),(31,45)]):
        self.niaFPS          = niaFPS
        self.deviceName      = deviceName
        self.bands           = bands

class RawVisualizationPanel(WXElements.GLCanvasBase):
   def InitGL(self):
       light_diffuse = [1.0, 1.0, 1.0, 1.0]
       light_position = [1.0, 1.0, 1.0, 0.0]
       glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
       glLightfv(GL_LIGHT0, GL_POSITION, light_position)
       glEnable(GL_LIGHTING)
       glEnable(GL_LIGHT0)
       glEnable(GL_DEPTH_TEST)
       glClearColor(0.0, 0.0, 0.0, 1.0)
       glClearDepth(1.0)
       glMatrixMode(GL_PROJECTION)
       glLoadIdentity()
       gluPerspective(40.0, 1.0, 1.0, 30.0)
       glMatrixMode(GL_MODELVIEW)
       glLoadIdentity()
       gluLookAt(0.0, 0.0, 10.0,
                 0.0, 0.0, 0.0,
                 0.0, 1.0, 0.0)
                 
   def OnDraw(self):
       glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
       glLoadIdentity()
       glEnableClientState(GL_VERTEX_ARRAY)
       for eachI in range(len(bciDevice.devices)):
           glColor(0.55,0.55,0.3)
           wave_array = []
           for historyIndex in xrange(499, -1, -1): #reversed(xrange(500)):
               wave_array =  wave_array +[[-1.0+ (2.0*float(historyIndex)/499.0), -1.0+((2.0*eachI)+(0.0000001*bciDevice.working_Data(eachI)[-1-historyIndex]))/len(bciDevice.devices)]]
           glVertexPointerf(wave_array)
           glDrawArrays(GL_LINE_STRIP, 0, len(wave_array))
       for eachI in range(len(bciDevice.devices)):
           glColor(0.55,0.55,0.3)
           glRasterPos2f(0.2 ,-0.5 +( (2.0*eachI))/len(bciDevice.devices))
           for eachChar in ''.join(["Device ",str(eachI)," Raw"]):
                  glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(eachChar))
       self.SwapBuffers()
       
   def newReading(self):
       if self.GetGrandParent().GetSelection()==0:
           self.SetCurrent()
           self.OnDraw()
           
   def resetReading(self):
       if self.GetGrandParent().GetSelection()==0:
           self.SetCurrent()
           self.OnDraw()

class FFTVisualizationPanel(WXElements.GLCanvasBase):
   def InitGL(self):
       light_diffuse = [1.0, 1.0, 1.0, 1.0]
       light_position = [1.0, 1.0, 1.0, 0.0]
       glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
       glLightfv(GL_LIGHT0, GL_POSITION, light_position)
       glEnable(GL_LIGHTING)
       glEnable(GL_LIGHT0)
       glEnable(GL_DEPTH_TEST)
       glClearColor(0.0, 0.0, 0.0, 1.0)
       glClearDepth(1.0)
       glMatrixMode(GL_PROJECTION)
       glLoadIdentity()
       gluPerspective(40.0, 1.0, 1.0, 30.0)
       glMatrixMode(GL_MODELVIEW)
       glLoadIdentity()
       gluLookAt(0.0, 0.0, 10.0,
                 0.0, 0.0, 0.0,
                 0.0, 1.0, 0.0)
                 
   def OnDraw(self):
       glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
       glLoadIdentity()
       glEnableClientState(GL_VERTEX_ARRAY)
       for eachI in range(len(bciDevice.devices)):
           for eachFingerI in range(len(settings.bands)):
               everyFingerI = (eachI*len(settings.bands)) + eachFingerI
               glColor(everyFingerI*0.05+0.3,-everyFingerI*0.05+0.9,float(everyFingerI%2))
               seg = bciDevice.frequencies(eachI,settings.bands[eachFingerI][0],settings.bands[eachFingerI][1])
               avg = sum(seg)/len(seg)
               wave_array = [[ -1.0+ (2.0*float(settings.bands[eachFingerI][0])/49.0) , -1.0+((2.0*eachI))/len(bciDevice.devices) ],
                             [ -1.0+ (2.0*float(settings.bands[eachFingerI][0])/49.0) , -1.0+((2.0*eachI) + avg)/len(bciDevice.devices)],
                             [ -1.0+ (2.0*float(settings.bands[eachFingerI][1])/49.0), -1.0+((2.0*eachI))/len(bciDevice.devices)],
                             [ -1.0+ (2.0*float(settings.bands[eachFingerI][1])/49.0), -1.0+((2.0*eachI) + avg)/len(bciDevice.devices)]]
               glVertexPointerf(wave_array)
               glDrawArrays(GL_QUAD_STRIP, 0, len(wave_array))
       for eachI in range(len(bciDevice.devices)):
           glColor(1.0,0.55,0.3)
           wave_array = []
           for freqs in reversed(xrange(50)):
               wave_array =  wave_array +[[-1.0+ (2.0*float(freqs)/49.0),  -1.0+((2.0*eachI)+(bciDevice.frequencies(eachI,0,50)[freqs]))/len(bciDevice.devices)]]
           glVertexPointerf(wave_array)
           glDrawArrays(GL_LINE_STRIP, 0, len(wave_array))
       for eachI in range(len(bciDevice.devices)):
           glColor(1.0,0.55,0.3)
           glRasterPos2f(0.2 ,-0.55 +( (2.0*eachI))/len(bciDevice.devices))
           for eachChar in ''.join(["Device ",str(eachI)," FFT"]):
                  glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(eachChar))
           glColor(0.55,0.55,0.55)
           glRasterPos2f(0.2 ,-0.60 +( (2.0*eachI))/len(bciDevice.devices))
           for eachChar in ''.join(["Device ",str(eachI)," EEG Bands"]):
                  glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(eachChar))
       self.SwapBuffers()
       
   def newReading(self):
       if self.GetGrandParent().GetSelection()==2:
           self.SetCurrent()
           self.OnDraw()
           
   def resetReading(self):
       if self.GetGrandParent().GetSelection()==2:
           self.SetCurrent()
           self.OnDraw()

class FFTHistoryVisualizationPanel(WXElements.GLCanvasBase):
   def __init__(self, parent):
       self.ylists = [[ 0.0 for each in xrange(len(settings.bands)*len(bciDevice.devices))] for every in range(100)]
       self.xlist = [float(i)/float(-1+len(self.ylists[0])) for i in xrange(len(self.ylists[0]))]
       WXElements.GLCanvasBase.__init__(self, parent)
       
   def InitGL(self):
       light_diffuse = [1.0, 1.0, 1.0, 1.0]
       light_position = [1.0, 1.0, 1.0, 0.0]
       glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
       glLightfv(GL_LIGHT0, GL_POSITION, light_position)
       glEnable(GL_LIGHTING)
       glEnable(GL_LIGHT0)
       glEnable(GL_DEPTH_TEST)
       glClearColor(0.0, 0.0, 0.0, 1.0)
       glClearDepth(1.0)
       glMatrixMode(GL_PROJECTION)
       glLoadIdentity()
       gluPerspective(40.0, 1.0, 1.0, 30.0)
       glMatrixMode(GL_MODELVIEW)
       glLoadIdentity()
       gluLookAt(0.0, 0.0, 10.0,
                 0.0, 0.0, 0.0,
                 0.0, 1.0, 0.0)
                 
   def OnDraw(self):
       glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
       glLoadIdentity()
       glEnableClientState(GL_VERTEX_ARRAY)
       for everyFingerI in range(len(settings.bands)*len(bciDevice.devices)):
           glColor(everyFingerI*0.05+0.3,-everyFingerI*0.05+0.9,float(everyFingerI%2))
           wave_array = []
           for historyIndex in xrange(100):
               wave_array.append([-1.0+ (2.0*float(historyIndex)/99.0), -0.9 + (0.1*everyFingerI) + (0.3 * self.ylists[historyIndex][everyFingerI])])
           glVertexPointerf(wave_array)
           glDrawArrays(GL_LINE_STRIP, 0, len(wave_array))
           glRasterPos2f(-0.95 ,-0.95 + (0.1*everyFingerI) )
           for eachChar in ''.join([
               "Device ",str(everyFingerI/len(settings.bands)),", Band ",str(everyFingerI%len(settings.bands)),": ", \
               str(settings.bands[everyFingerI%len(settings.bands)][0]),"-", \
               str(settings.bands[everyFingerI%len(settings.bands)][1])," Hz"]):
                  glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(eachChar))
       self.SwapBuffers()
       
   def newReading(self):
       newReadings = [] 
       for eachDeviceI in range(len(bciDevice.devices)):
           for eachFingerIndex in range(len(settings.bands)):
               fingerlist = bciDevice.frequencies(eachDeviceI,settings.bands[eachFingerIndex][0],settings.bands[eachFingerIndex][1])
               newReadings.append(float(sum(fingerlist))/float(len(fingerlist)))
       self.ylists = [newReadings]+self.ylists[0:99]
       if self.GetGrandParent().GetSelection()==3:
           self.SetCurrent()
           self.OnDraw()
           
   def resetReading(self):
       self.ylists = [[0.0 for each in xrange(len(settings.bands)*len(bciDevice.devices))] for every in range(100)]
       if self.GetGrandParent().GetSelection()==3:
           self.SetCurrent()
           self.OnDraw()

class SpectogramVisualizationPanel(WXElements.GLCanvasBase):
   def __init__(self, parent):
       WXElements.GLCanvasBase.__init__(self, parent)
       self.historyLength = 5
       self.colorlists = [[ self.spectralColor(0.0) for each in xrange(50*len(bciDevice.devices))] for every in xrange(self.historyLength)]
       xlist = [-1.0+(2.0*float(i)/float(-1+self.historyLength)) for i in xrange(self.historyLength)]
       ylist = [-1.0+(2.0*float(i)/float(-1+len(self.colorlists[0]))) for i in xrange(len(self.colorlists[0]))]
       columns = []
       self.quadCols = []
       for historyIndex in xrange(self.historyLength):
           x = xlist[historyIndex]
           columns.append([[x,y] for y in ylist])
       for historyIndex in xrange(self.historyLength-1):
           self.quadCols.append(zip ( columns[historyIndex] , columns[historyIndex+1]))
       self.spectralColorColumHistory = []
       for historyIndex in xrange(self.historyLength-1):
           self.spectralColorColumHistory.append(zip ( self.colorlists[historyIndex] , self.colorlists[historyIndex+1]))
           
   def InitGL(self):
       light_diffuse = [1.0, 1.0, 1.0, 1.0]
       light_position = [1.0, 1.0, 1.0, 0.0]
       glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
       glLightfv(GL_LIGHT0, GL_POSITION, light_position)
       glEnable(GL_LIGHTING)
       glEnable(GL_LIGHT0)
       glEnable(GL_DEPTH_TEST)
       glClearColor(0.0, 0.0, 0.0, 1.0)
       glClearDepth(1.0)
       glMatrixMode(GL_PROJECTION)
       glLoadIdentity()
       gluPerspective(40.0, 1.0, 1.0, 30.0)
       glMatrixMode(GL_MODELVIEW)
       glLoadIdentity()
       gluLookAt(0.0, 0.0, 10.0,
                 0.0, 0.0, 0.0,
                 0.0, 1.0, 0.0)
                 
   def OnDraw(self):
       glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
       glLoadIdentity()
       glEnableClientState(GL_VERTEX_ARRAY)
       glEnableClientState(GL_COLOR_ARRAY)
       for historyIndex in xrange(self.historyLength-1):
           glVertexPointerf(self.quadCols[historyIndex])
           glColorPointerf(self.spectralColorColumHistory[historyIndex])
           glDrawArrays(GL_QUAD_STRIP, 0, 100*len(bciDevice.devices))
       self.SwapBuffers()
       
   def newReading(self):
       newReadings = [] 
       for eachDeviceI in range(len(bciDevice.devices)):
           newReadings.extend(bciDevice.frequencies(eachDeviceI,0,50))
       self.colorlists = [map(self.spectralColor,newReadings)]+self.colorlists[0:(self.historyLength-1)]
       self.spectralColorColumHistory = [ zip ( self.colorlists[0] , self.colorlists[1])
                 ]+self.spectralColorColumHistory[0:(self.historyLength-2)]
       if self.GetGrandParent().GetSelection()==1:
           self.SetCurrent()
           self.OnDraw()
           
   def resetReading(self):
       self.colorlists = [[ self.spectralColor(0.0) for each in xrange(50*len(bciDevice.devices))] for every in xrange(self.historyLength)]
       xlist = [-1.0+(2.0*float(i)/float(-1+self.historyLength)) for i in xrange(self.historyLength)]
       ylist = [-1.0+(2.0*float(i)/float(-1+len(self.colorlists[0]))) for i in xrange(len(self.colorlists[0]))]
       columns = []
       self.quadCols = []
       for historyIndex in xrange(self.historyLength):
           x = xlist[historyIndex]
           columns.append([[x,y] for y in ylist])
       for historyIndex in xrange(self.historyLength-1):
           self.quadCols.append(zip ( columns[historyIndex] , columns[historyIndex+1]))
       self.spectralColorColumHistory = []
       for historyIndex in xrange(self.historyLength-1):
           self.spectralColorColumHistory.append(zip ( self.colorlists[historyIndex] , self.colorlists[historyIndex+1]))
       if self.GetGrandParent().GetSelection()==1:
           self.SetCurrent()
           self.OnDraw()
           
   def spectralColor(self,v):
       if v <= 0.0:
           return [0.0,0.0,0.0]
       elif v <= 0.2:
           return [0.0,0.0,v*5.0]
       elif v <= 0.5:
           return [(v-0.2)/0.3,0.0,1.0]
       elif v <= 1.5:
           return [1.0,0.0,1.0-(v-0.5)]
       elif v <= 11.5:
           return [1.0,((v-1.5)*0.05),0.0]
       return [1.0,1.0,((v-11.5)*0.008)]

class SettingsPanel(wx.Panel):
    def __init__(self, parent):        
        wx.Panel.__init__(self, parent)
        self.fpsField = wx.TextCtrl(self,value=str(settings.niaFPS))
        self.fpsField.Bind(wx.EVT_KILL_FOCUS, self.fpsChanged)
        panelSizer = wx.FlexGridSizer(0,10,0,0)
        panelSizer.AddGrowableCol(0)
        panelSizer.Add(wx.StaticText(self,label=""), 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(wx.StaticText(self,label="Samples per second:"), 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(self.fpsField, 0, wx.EXPAND, 5)
        panelSizer.AddGrowableCol(3)
        panelSizer.Add(wx.StaticText(self,label=""), 0, wx.ALIGN_CENTER, 5)
        self.bandChoice = wx.Choice(self,choices=["EEG Band "+str(i) for i in xrange(9)])
        panelSizer.Add(self.bandChoice, 0, wx.ALIGN_CENTER, 5)
        self.bandChoice.Bind(wx.EVT_CHOICE, self.bandChanged)
        self.fromFreqField = wx.TextCtrl(self,value=str(settings.bands[0][0]))
        panelSizer.Add(self.fromFreqField, 0, wx.EXPAND, 5)
        self.fromFreqField.Bind(wx.EVT_KILL_FOCUS, self.freqChanged)
        panelSizer.Add(wx.StaticText(self,label="-"), 0, wx.ALIGN_CENTER, 5)
        self.toFreqField = wx.TextCtrl(self,value=str(settings.bands[0][1]))
        panelSizer.Add(self.toFreqField, 0, wx.EXPAND, 5)
        self.toFreqField.Bind(wx.EVT_KILL_FOCUS, self.freqChanged)
        panelSizer.Add(wx.StaticText(self,label="Hz"), 0, wx.ALIGN_CENTER, 5)
        panelSizer.AddGrowableCol(9)
        panelSizer.Add(wx.StaticText(self,label=""), 0, wx.ALIGN_CENTER, 5)
        self.SetSizer(panelSizer)
        self.SetAutoLayout(1)
        
    def fpsChanged(self, event):
        val = 0
        try:
                val = int(self.fpsField.GetValue())
        except ValueError:
                val = settings.niaFPS
        if (val<1):
                val = 1
        elif (val>50):
                val = 50
        settings.niaFPS = val
        self.fpsField.SetValue(str(val))
        self.GetGrandParent().timer.Stop()
        bciDevice.setPoints(int(500.0/settings.niaFPS))
        self.GetGrandParent().timer.Start(int(1000.0/settings.niaFPS))
        event.Skip()
        
    def bandChanged(self, event):
        i = self.bandChoice.GetSelection()
        self.fromFreqField.SetValue(str(settings.bands[i][0]))
        self.toFreqField.SetValue(str(settings.bands[i][1]))
        event.Skip()
        
    def freqChanged(self, event):
        i = self.bandChoice.GetSelection()
        fr = 0
        try:
                fr = int(self.fromFreqField.GetValue())
        except ValueError:
                fr = settings.bands[i][0]
        if (fr<0):
                fr = 0
        elif (fr>100):
                fr = 100
        to = 0
        try:
                to = int(self.toFreqField.GetValue())
        except ValueError:
                to = settings.bands[i][1]
        if (to<0):
                to = 0
        elif (to>100):
                to = 100
        if to<fr:
            #sw = fr
            #fr = to
            #to = sw
            sw, fr, to = fr, to, sw
        elif to == fr:
            to += 2
        if abs(to-fr) == 1:
            to += 1
        self.fromFreqField.SetValue(str(fr))
        self.toFreqField.SetValue(str(to))
        settings.bands[i] = (fr,to)
        event.Skip()

class GUIMain(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,None,title="Triathlon Analyzer",size=(600,600))
        self.panel = wx.Panel(self, wx.ID_ANY)
        MenuBar = wx.MenuBar()
        self.FileMenu = wx.Menu()
        item = self.FileMenu.Append(wx.ID_ANY, text="Calibrate")
        self.Bind(wx.EVT_MENU, self.OnCalibrate, item)
        item = self.FileMenu.Append(wx.ID_EXIT, text="Quit")
        self.Bind(wx.EVT_MENU, self.OnQuit, item)
        MenuBar.Append(self.FileMenu, "Menu")
        self.SetMenuBar(MenuBar)
        sizer = wx.FlexGridSizer(2,1,0,0)
        self.settingsPanel = SettingsPanel(self.panel)
        self.tabs = wx.Notebook(self.panel)
        rawvisualizationPanel = wx.Panel(self.tabs, wx.ID_ANY)
        rawvisualizationSizer = wx.FlexGridSizer(1,1,0,0)
        rawvisualizationSizer.AddGrowableRow(0)
        rawvisualizationSizer.AddGrowableCol(0)
        if noGL:
            self.rawvisualizationCanvas = WXElements.NoGLVisualizationPanel(rawvisualizationPanel)
        else: 
            self.rawvisualizationCanvas = RawVisualizationPanel(rawvisualizationPanel)
        rawvisualizationSizer.Add(self.rawvisualizationCanvas , 1, wx.EXPAND)
        rawvisualizationPanel.SetSizer(rawvisualizationSizer)
        visualizationPanel = wx.Panel(self.tabs, wx.ID_ANY)
        visualizationSizer = wx.FlexGridSizer(1,1,0,0)
        visualizationSizer.AddGrowableRow(0)
        visualizationSizer.AddGrowableCol(0)
        if noGL:
            self.visualizationCanvas = WXElements.NoGLVisualizationPanel(visualizationPanel)
        else: 
            self.visualizationCanvas = FFTVisualizationPanel(visualizationPanel)
        visualizationSizer.Add(self.visualizationCanvas , 1, wx.EXPAND)
        visualizationPanel.SetSizer(visualizationSizer)
        historyPanel = wx.Panel(self.tabs, wx.ID_ANY)
        historySizer = wx.FlexGridSizer(1,1,0,0)
        historySizer.AddGrowableRow(0)
        historySizer.AddGrowableCol(0)
        if noGL:
            self.historyCanvas = WXElements.NoGLVisualizationPanel(historyPanel)
        else: 
            self.historyCanvas = FFTHistoryVisualizationPanel(historyPanel)
        historySizer.Add(self.historyCanvas , 1, wx.EXPAND)
        historyPanel.SetSizer(historySizer)
        spectogramPanel = wx.Panel(self.tabs, wx.ID_ANY)
        spectogramSizer = wx.FlexGridSizer(1,1,0,0)
        spectogramSizer.AddGrowableRow(0)
        spectogramSizer.AddGrowableCol(0)
        if noGL:
            self.spectogramCanvas = WXElements.NoGLVisualizationPanel(spectogramPanel)
        else: 
            self.spectogramCanvas = SpectogramVisualizationPanel(spectogramPanel)
        spectogramSizer.Add(self.spectogramCanvas , 1, wx.EXPAND)
        spectogramPanel.SetSizer(spectogramSizer)
        self.tabs.AddPage(rawvisualizationPanel,"Raw")
        self.tabs.AddPage(spectogramPanel,"Spectogram")
        self.tabs.AddPage(visualizationPanel,"EEG Bands")
        self.tabs.AddPage(historyPanel,"EEG Band History")
        sizer.AddGrowableCol(0)
        sizer.Add(wx.StaticText(self.panel,label=""), 0, wx.ALIGN_CENTER, 5)
        sizer.Add(self.settingsPanel , 1, wx.EXPAND)
        sizer.Add(wx.StaticText(self.panel,label=""), 0, wx.ALIGN_CENTER, 5)
        sizer.AddGrowableRow(3)
        sizer.Add(self.tabs , 1, wx.EXPAND)
        self.panel.SetSizer(sizer)
        self.panel.SetAutoLayout(1)
        self.timer = wx.Timer(self, wx.ID_ANY)
        self.Bind(wx.EVT_TIMER, self.NiaUpdate, self.timer)
        
    def OnQuit(self, event):
        self.timer.Stop()
        self.Close()
        
    def OnCalibrate(self, event):
        bciDevice.calibrateAll()
        event.Skip()
        
    def NiaUpdate(self, ev):
        if bciDevice.deviceType == InputManager.OCZ_NIAx2:
            data_thread = threading.Thread(target=bciDevice.record,args=([0]))
            data_thread2 = threading.Thread(target=bciDevice.record,args=([1]))
            data_thread.start()
            data_thread2.start()
            bciDevice.process(0)
            bciDevice.process(1)
        else:
            data_thread = threading.Thread(target=bciDevice.record,args=([0]))
            data_thread.start()
            bciDevice.process(0)
        self.rawvisualizationCanvas.newReading()
        self.spectogramCanvas.newReading()
        self.visualizationCanvas.newReading()
        self.historyCanvas.newReading()
        ev.Skip()

class NiaEEGApp(wx.App):
    def __init__(self, redirect = False):
        wx.App.__init__(self)
        self.mainWindow = GUIMain()
        self.mainWindow.Show(True)
        bciDevice.setPoints(int(500.0/settings.niaFPS))
        self.mainWindow.timer.Start(int(1000.0/settings.niaFPS))

if __name__ == "__main__":
        settings = AppSettings()
        selection = WXElements.selection("Select your Device",InputManager.SupportedDevices.keys()[0],InputManager.SupportedDevices.keys())
        settings.deviceName = selection
        bciDevice = InputManager.BCIDevice(settings.deviceName)
        argcp = ''
        glutInit(argcp, sys.argv)
        niaEEGApp = NiaEEGApp()
        niaEEGApp.MainLoop()
