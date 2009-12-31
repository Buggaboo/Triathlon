#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

# Howto, Code license, Credits, etc: http://code.google.com/B/BCI-Project-Triathlon/

noGL = False   # Set noGL to True for disabling the use of OpenGL (to gain speed, or to avoid python-wx-opengl problems)


from pyfann import libfann
import os
import math
import pickle
import wx
import numpy
import usb
import sys
import threading
from mdp import Flow
from mdp.nodes import PCANode

import InputManager
import OutputManager
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

class OutputChannel():
    def __init__(self,
                channelName,
                includeInOutput =  True,
                outputKeyList   =  [],
                lowThreshold    = -0.5,
                highThreshold   =  0.5,
                allSamples      = True):
        self.channelName     = channelName
        self.includeInOutput = includeInOutput
        self.outputKeyList   = outputKeyList
        self.lowThreshold    = lowThreshold
        self.highThreshold   = highThreshold
        self.allSamples      = allSamples

class Current_Data():
    def __init__(self):
        self.outputMode = False
        self.currentReducedSample = []
        self.output = []

class ProfileSettings():
    def __init__(self,
                 freqRange              = (0,0),
                 timeTailLength         = 0,
                 niaFPS                 = 0,
                 flowTrainingChunckSize = 0,
                 trainingClusterSize    = 0,
                 testClusterSize        = 0,
                 profileName            = "",
                 dimensionReductionFlow = "",
                 channels               = []):
        self.freqRange              = freqRange
        self.timeTailLength         = timeTailLength
        self.niaFPS                 = niaFPS,
        self.flowTrainingChunckSize = flowTrainingChunckSize
        self.trainingClusterSize    = trainingClusterSize
        self.profileName            = profileName
        self.dimensionReductionFlowLabel = dimensionReductionFlow
        self.dimensionReductionFlow = Flow([])
        self.channels               = channels
        self.qfEnabled              = False
        self.qfAction                  = ""
        self.qfThreshold            = 0.0
    
class ChannelCanvas(WXElements.GLCanvasBase):
    def __init__(self, parent,channelIndex):
       self.channelIndex = channelIndex
       self.xlist = [0.0 for each in range(30)]
       self.ylist = [-1.0+(2.0*(float(i)/float(29))) for i in range(30)]
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
       c = (0.3,0.3,1.3)
       if not(profile.channels[self.channelIndex].includeInOutput):
            c = (c[0]*0.35,c[1]*0.35,c[2]*0.35)
       glColor(c[0],c[1],c[2])
       glVertexPointerf([
                        [-1.0 ,1.0],
                        [-1.0 ,-1.0],
                        [profile.channels[self.channelIndex].lowThreshold * 0.95,1.0],
                        [profile.channels[self.channelIndex].lowThreshold * 0.95,-1.0]])
       glDrawArrays(GL_QUAD_STRIP, 0, 4)
       glVertexPointerf([
                        [profile.channels[self.channelIndex].highThreshold * 0.95,1.0],
                        [profile.channels[self.channelIndex].highThreshold * 0.95,-1.0],
                        [1.0,1.0],
                        [1.0,-1.0]])
       glDrawArrays(GL_QUAD_STRIP, 0, 4)
       c = (0.8,0.8,0.8)
       if not(profile.channels[self.channelIndex].includeInOutput):
            c = (0.2,0.2,0.2)
       glColor(c[0],c[1],c[2])
       glVertexPointerf([[self.xlist[i] * 0.95 , self.ylist[i]] for i in range(30)])
       glDrawArrays(GL_LINE_STRIP, 0, 30)
       self.SwapBuffers()
       
    def newReading(self):
        self.xlist = ([current.output[self.channelIndex]]+self.xlist)[0:-1]
        self.Refresh()
        self.Update()

class ChannelPanel(wx.Panel):
    def __init__(self, parent, channelIndex):        
        wx.Panel.__init__(self, parent)
        panelSizer = wx.FlexGridSizer(0,1,0,0)
        panelSizer.AddGrowableCol(0)
        self.includeCB = wx.CheckBox(self,label="include in output")
        self.includeCB.SetValue(profile.channels[channelIndex].includeInOutput)
        self.includeCB.Bind(wx.EVT_CHECKBOX, self.IncludeChanged)
        panelSizer.Add(self.includeCB, 0, wx.ALIGN_CENTER, 5)
        labelPanel = wx.Panel(self)
        labelSizer = wx.FlexGridSizer(0,2,0,0)
        labelSizer.AddGrowableCol(0)
        labelSizer.Add(wx.StaticText(labelPanel,label=profile.channels[channelIndex].outputKeyList[0][0]), 0, wx.ALIGN_LEFT, 5)
        labelSizer.AddGrowableCol(1)
        labelSizer.Add(wx.StaticText(labelPanel,label=profile.channels[channelIndex].outputKeyList[1][0]), 0, wx.ALIGN_RIGHT, 5)
        self.lowChoice = wx.Choice(labelPanel, choices=keycodelistlabels)
        position = self.lowChoice.FindString("Action: "+profile.channels[channelIndex].outputKeyList[0][2]) 
        self.lowChoice.SetSelection (position)
        self.lowChoice.Bind(wx.EVT_CHOICE, self.LowKeycodeChanged)
        labelSizer.Add(self.lowChoice, 0, wx.ALIGN_LEFT, 5)
        self.highChoice = wx.Choice(labelPanel, choices=keycodelistlabels)
        position = self.highChoice.FindString("Action: "+profile.channels[channelIndex].outputKeyList[1][2]) 
        self.highChoice.SetSelection (position)        
        self.highChoice.Bind(wx.EVT_CHOICE, self.HighKeycodeChanged)
        labelSizer.Add(self.highChoice, 0, wx.ALIGN_RIGHT, 5)
        labelPanel.SetSizer(labelSizer)
        panelSizer.Add(labelPanel, 0, wx.EXPAND, 5)
        self.lowSlider = wx.Slider(self, maxValue=1000)
        self.lowSlider.SetValue(500+int(round(profile.channels[channelIndex].lowThreshold*500.0)))
        self.lowSlider.Bind(wx.EVT_SLIDER,self.LowChanged)
        panelSizer.Add(self.lowSlider, 0, wx.EXPAND, 5)
        self.highSlider =  wx.Slider(self, maxValue=1000, style=wx.SL_INVERSE)
        self.highSlider.SetValue(500-int(round(profile.channels[channelIndex].highThreshold*500.0)))
        self.highSlider.Bind(wx.EVT_SLIDER,self.HighChanged)
        panelSizer.Add(self.highSlider, 0, wx.EXPAND, 5)
        self.canvas = ''
        if noGL:
            self.canvas = WXElements.NoGLVisualizationPanel(self)
        else:
            self.canvas = ChannelCanvas(self,channelIndex)
        panelSizer.AddGrowableRow(4)
        panelSizer.Add(self.canvas, 0, wx.EXPAND, 5)
        self.currentSlider =  wx.Slider(self, maxValue=1000)
        panelSizer.Add(self.currentSlider, 0, wx.EXPAND, 5)
        self.SetSizer(panelSizer)
        self.SetAutoLayout(1)
        self.channelIndex = channelIndex
        
    def IncludeChanged(self, event):
        profile.channels[self.channelIndex].includeInOutput = self.includeCB.IsChecked()
        event.Skip()
        
    def LowChanged(self, event):
        profile.channels[self.channelIndex].lowThreshold = (float(self.lowSlider.GetValue()) - 500.0) / 500.0
        if profile.channels[self.channelIndex].lowThreshold > profile.channels[self.channelIndex].highThreshold:
            self.highSlider.SetValue(1000-self.lowSlider.GetValue())
            profile.channels[self.channelIndex].highThreshold = profile.channels[self.channelIndex].lowThreshold
        event.Skip()
        
    def HighChanged(self, event):
        profile.channels[self.channelIndex].highThreshold = (-float(self.highSlider.GetValue()) + 500.0) / 500.0
        if profile.channels[self.channelIndex].lowThreshold > profile.channels[self.channelIndex].highThreshold:
            self.lowSlider.SetValue(1000-self.highSlider.GetValue())
            profile.channels[self.channelIndex].lowThreshold = profile.channels[self.channelIndex].highThreshold
        event.Skip()
        
    def LowKeycodeChanged(self, event):
        profile.channels[self.channelIndex].outputKeyList[0] = (profile.channels[self.channelIndex].outputKeyList[0][0],
                                                                 profile.channels[self.channelIndex].outputKeyList[0][1], 
                                                                 self.lowChoice.GetStringSelection()[8:])
        event.Skip()
        
    def HighKeycodeChanged(self, event):
        profile.channels[self.channelIndex].outputKeyList[1] = (profile.channels[self.channelIndex].outputKeyList[1][0],
                                                                 profile.channels[self.channelIndex].outputKeyList[1][1],
                                                                 self.highChoice.GetStringSelection()[8:])
        event.Skip()

class SettingPanel(wx.Panel):
    def __init__(self, parent):        
        wx.Panel.__init__(self, parent)
        panelSizer = wx.FlexGridSizer(0,1,0,0)
        panelSizer.AddGrowableCol(0)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(wx.StaticText(self,label=("Profile name: "+profile.profileName)), 0, wx.ALIGN_LEFT, 5)
        qfPanel = wx.Panel(self)
        qfSizer = wx.FlexGridSizer(0,1,0,0)
        self.qfCheckbox = wx.CheckBox(qfPanel,label="include Quickfire")
        self.qfCheckbox.SetValue(profile.qfEnabled)
        self.qfCheckbox.Bind(wx.EVT_CHECKBOX, self.qfEnabledChanged)
        qfSizer.AddGrowableCol(0)
        qfSizer.Add(self.qfCheckbox, 0, wx.ALIGN_RIGHT, 5)
        self.qfActionChoice = wx.Choice(qfPanel, choices=keycodelistlabels)
        position = self.qfActionChoice.FindString("Action: "+profile.qfAction) 
        self.qfActionChoice.SetSelection (position)        
        self.qfActionChoice.Bind(wx.EVT_CHOICE, self.qfActioncodeChanged)
        qfSizer.Add(self.qfActionChoice, 0, wx.ALIGN_RIGHT, 5)
        qfPanel.SetSizer(qfSizer)
        self.outputButton = wx.Button(self, id=-1, label="Start Output ( Ctrl F11 )")
        self.outputButton.Bind(wx.EVT_BUTTON, self.SwitchOutput)
        panelSizer.Add(self.outputButton, 0, wx.EXPAND, 5)
        panelSizer.Add(qfPanel, 0, wx.EXPAND, 5)
        self.nb = wx.Notebook(self)
        self.channelPanels = []
        for channelIndex in range(len(profile.channels)):
                self.channelPanels.append(ChannelPanel(self.nb,channelIndex))
                self.nb.AddPage(self.channelPanels[channelIndex],profile.channels[channelIndex].channelName)
        panelSizer.AddGrowableRow(4)
        panelSizer.Add(self.nb, 0, wx.EXPAND, 5)
        self.SetSizer(panelSizer)
        self.SetAutoLayout(1)
        
    def SwitchOutput(self, event):
        if current.outputMode:
            current.outputMode=False
            self.releaseAll()
        else:
            current.outputMode=True
            bciDevice.calibrateAll()            
        fannToOutputApp.setIcon()
        event.Skip()
        
    def releaseAll(self):
        for channelIndex in range(len(profile.channels)):
            self.releaseAllinChannel(channelIndex)
            
    def releaseAllinChannel(self,channelIndex):
        for (clName,cond,keystr) in profile.channels[channelIndex].outputKeyList:
            inputFaker.keyRelease(keystr)
        inputFaker.flush()
        
    def newReading(self):
        for channelIndex in range(len(profile.channels)):
                self.channelPanels[channelIndex].canvas.newReading()
                self.channelPanels[channelIndex].currentSlider.SetValue(500 + int(round(500.0 * current.output[channelIndex])))
                
    def qfActioncodeChanged(self, event):
        profile.qfAction = self.qfActionChoice.GetStringSelection()[8:]
        event.Skip()
        
    def qfEnabledChanged(self, event):
        profile.qfEnabled = self.qfCheckbox.IsChecked()
        event.Skip()

class VisualizationPanel(WXElements.GLCanvasBase):
   def InitGL(self):
       self.maxScaler = 30.0
       self.spacer = 0.02
       self.field = 0.16
       self.raw = [ [1.0,1.0,1.0] for each in xrange(50)]
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
       glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
       glLoadIdentity();
       glEnableClientState(GL_VERTEX_ARRAY)
       c = (0.45,0.45,0.0)
       if not (profile.qfEnabled):
                    c = (c[0]*0.35,c[1]*0.35,c[2]*0.35)
       glColor(c[0],c[1],c[2])
       wave_array = []
       for historyIndex in reversed(xrange(50)):
           wave_array =  wave_array +[[-1.0+ (2.0*float(historyIndex)/49.0), -1.0 +(self.raw[historyIndex][2] *(self.raw[historyIndex][1] - self.raw[historyIndex][0]))]]+[[-1.0+ (2.0*float(historyIndex)/49.0), -1.0 ]]
       glVertexPointerf(wave_array)
       glDrawArrays(GL_QUAD_STRIP, 0, len(wave_array))
       wave_array = []
       glColor(1.0,1.0,0.0)  
       wave_array = [ [math.cos(float(i)*2*math.pi/len(current.currentReducedSample))* (0.2+(current.currentReducedSample[i]/self.maxScaler)),
                              math.sin(float(i)*2*math.pi/len(current.currentReducedSample))* (0.2+(current.currentReducedSample[i]/self.maxScaler))]
                          for i in range(len(current.currentReducedSample))]
       if (len(wave_array)>0):
                  wave_array.append(wave_array[0])
                  glVertexPointerf(wave_array)
                  glDrawArrays(GL_LINE_STRIP, 0, len(wave_array))
       for channelIndex in range(len(current.output)):
           for i in range(3):
                c = (0.0,0.0,0.0)
                if (i==2) and (current.output[channelIndex]<profile.channels[channelIndex].lowThreshold):
                    c = (0.3,0.3,1.0)
                elif (i==0) and (current.output[channelIndex]>profile.channels[channelIndex].highThreshold):
                    c = (0.3,0.3,1.0)
                elif (i==1) and not((current.output[channelIndex]<profile.channels[channelIndex].lowThreshold) or 
                                    (current.output[channelIndex]>profile.channels[channelIndex].highThreshold)):
                    c = (0.3,0.3,1.0)
                else:
                    c = (0.3,0.3,0.3)
                if not (profile.channels[channelIndex].includeInOutput):
                    c = (c[0]*0.35,c[1]*0.35,c[2]*0.35)
                glColor(c[0],c[1],c[2])
                center = (  1.0 - ((self.spacer * (1.0+float(i)) )+(self.field * (0.5+float(i)) ) ),
                            1.0 - ((self.spacer * (1.0+float(channelIndex)) )+(self.field * (0.5+float(channelIndex)) )))
                glVertexPointerf([
                        [center[0] + (0.5 * self.field),center[1] + (0.5 * self.field)],
                        [center[0] + (0.5 * self.field),center[1] - (0.5 * self.field)],
                        [center[0] - (0.5 * self.field),center[1] + (0.5 * self.field)],
                        [center[0] - (0.5 * self.field),center[1] - (0.5 * self.field)]])
                glDrawArrays(GL_QUAD_STRIP, 0, 4)
           if not (profile.channels[channelIndex].includeInOutput):
               glColor(0.35,0.35,0.35)
           else:
               glColor(0.85,0.85,0.85)
           glRasterPos2f(-1.0 + (self.spacer * 2.0 ),
                         1.0 - ((self.spacer * (1.0+float(channelIndex)) )+(self.field * (0.5+float(channelIndex)) )) -  6.0/self.height)
           try:   
              for eachChar in profile.channels[channelIndex].channelName:
                  glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(eachChar))
           except IndexError:
               pass
       c = (0.3,0.3,0.3)
       if  (self.raw[0][2] *(self.raw[0][1] - self.raw[0][0])) >= (2.0*profile.qfThreshold):
          c = (0.9,0.5,0.0)
       if not (profile.qfEnabled):
          c = (c[0]*0.35,c[1]*0.35,c[2]*0.35)
       glColor(c[0],c[1],c[2])
       glVertexPointerf([[-1.0,-1.0+(2.0*profile.qfThreshold)],[1.0,-1.0+(2.0*profile.qfThreshold)]])
       glDrawArrays(GL_LINE_STRIP, 0, 2)
       self.SwapBuffers()
       
   def newReading(self):
        self.raw = [ [ float(min(bciDevice.working_Data(0)[-385:-1]))/ float(bciDevice.calibration(0)), 
                     float(max(bciDevice.working_Data(0)[-385:-1]))/ float(bciDevice.calibration(0)),
                     float(sum(bciDevice.working_Data(0)[-385:-1])/385)/ float(bciDevice.calibration(0))] ]+self.raw[0:49]
        if self.GetParent().IsShown():
           self.SetCurrent()
           glViewport(0, 0, self.width, self.height)
           self.OnDraw()

class GUIMain(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,None,title="nia Triathlon Player",size=(1024,400))
        self.panel = wx.Panel(self, wx.ID_ANY)
        MenuBar = wx.MenuBar()
        self.FileMenu = wx.Menu()
        item = self.FileMenu.Append(wx.ID_ANY, text="Calibrate")
        self.Bind(wx.EVT_MENU, self.OnCalibrate, item)
        item = self.FileMenu.Append(wx.ID_ANY, text="Save Profile")
        self.Bind(wx.EVT_MENU, self.OnSave, item)
        item = self.FileMenu.Append(wx.ID_EXIT, text="Quit")
        self.Bind(wx.EVT_MENU, self.OnQuit, item)
        MenuBar.Append(self.FileMenu, "Menu")
        self.SetMenuBar(MenuBar)
        self.currentTopPanel = SettingPanel(self.panel)
        self.visualizationPanel = ''
        if noGL:
            self.visualizationPanel = WXElements.NoGLVisualizationPanel(self.panel)
        else: 
            self.visualizationPanel = VisualizationPanel(self.panel)
        sizer = wx.FlexGridSizer(1,3,4,4)
        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)
        sizer.Add(self.currentTopPanel, 1, wx.EXPAND)
        self.qfThresholdSlider = wx.Slider(self.panel,maxValue=1000,style=wx.SL_VERTICAL|wx.SL_INVERSE)
        self.qfThresholdSlider.SetValue(-30+int(profile.qfThreshold*1060.0))
        self.qfThresholdSlider.Bind(wx.EVT_SLIDER,self.qfChanged)
        sizer.Add(self.qfThresholdSlider, 1, wx.EXPAND)
        sizer.AddGrowableCol(2)
        sizer.Add(self.visualizationPanel, 1, wx.EXPAND)
        self.panel.SetSizer(sizer)
        self.panel.Layout()
        self.currentReadingsAndTail = [ bciDevice.frequenciesCombined(profile.freqRange[0],profile.freqRange[1])
                                                        for eachIndex in range(profile.timeTailLength+1)]
        self.timer = wx.Timer(self, wx.ID_ANY)
        
        self.Bind(wx.EVT_TIMER, self.NiaUpdate, self.timer)
    def OnQuit(self, event):
        self.timer.Stop()
        self.Close()
        
    def OnCalibrate(self, event):
        bciDevice.calibrateAll()
        event.Skip()
        
    def OnSave(self, event):
        if os.path.exists(profile.profileName+".profile"):
            os.remove(profile.profileName+".profile")
        workfile = open(profile.profileName+".profile", "w")
        pickle.dump(profile, workfile)
        workfile.close()
        event.Skip()
        
    def qfChanged(self, event):
        profile.qfThreshold = (float(30+self.qfThresholdSlider.GetValue())/1060.0)
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
        self.currentReadingsAndTail = [
                    bciDevice.frequenciesCombined(profile.freqRange[0],profile.freqRange[1])]+self.currentReadingsAndTail[0:profile.timeTailLength]
        sample=[]
        [sample.extend(i) for i in self.currentReadingsAndTail]
        if profile.dimensionReductionFlowLabel=="None":
                    current.currentReducedSample = sample
        else:
                current.currentReducedSample = profile.dimensionReductionFlow(numpy.array([sample]))[0]
        current.output = ann.run(current.currentReducedSample)
        wait=False
        if len(self.currentReadingsAndTail) < (1+profile.timeTailLength) :
            wait = True
        if not(wait):
            self.visualizationPanel.newReading()
            self.currentTopPanel.newReading()
        if (wx.GetKeyState(wx.WXK_CONTROL) and wx.GetKeyState(wx.WXK_F12)): 
            if current.outputMode:                     # switch output-mode off
                current.outputMode=False
                fannToOutputApp.setIcon()
                self.currentTopPanel.releaseAll()
        elif (wx.GetKeyState(wx.WXK_CONTROL) and wx.GetKeyState(wx.WXK_F11)):
            if not(current.outputMode):                # switch output-mode on
                current.outputMode=True
                fannToOutputApp.setIcon()
                bciDevice.calibrateAll()
        if current.outputMode:
            if (profile.qfEnabled):
                if (profile.qfThreshold*2.0) <= float(sum(bciDevice.working_Data(0)[-385:-1])/385)/ float(bciDevice.calibration(0)
                                                )*(float(max(bciDevice.working_Data(0)[-385:-1]))/ float(bciDevice.calibration(0)
                                                )-float(min(bciDevice.working_Data(0)[-385:-1]))/ float(bciDevice.calibration(0))):
                        inputFaker.keyHold(profile.qfAction)
                else:
                        inputFaker.keyRelease(profile.qfAction)
            for channelIndex in range(len(profile.channels)):
                if profile.channels[channelIndex].includeInOutput:
                          out = current.output[channelIndex]
                          if (out < profile.channels[channelIndex].lowThreshold):
                              inputFaker.keyHold(profile.channels[channelIndex].outputKeyList[0][2])
                          else:
                              inputFaker.keyRelease(profile.channels[channelIndex].outputKeyList[0][2])
                          if (out > profile.channels[channelIndex].highThreshold):
                              inputFaker.keyHold(profile.channels[channelIndex].outputKeyList[1][2])
                          else:
                              inputFaker.keyRelease(profile.channels[channelIndex].outputKeyList[1][2])
            inputFaker.flush()
        ev.Skip()

class FannToOutputApp(wx.App):
    def __init__(self, redirect = False):
        wx.App.__init__(self)
        ib = wx.IconBundle()
        bmp = self.make_grad_image(32,32, (0,0,0), (0,0,0))
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(bmp)
        ib.AddIcon(icon)
        self.mainWindow = GUIMain()
        self.mainWindow.SetIcons(ib)
        self.mainWindow.Show(True)
        bciDevice.setPoints(int(500.0/profile.niaFPS))
        self.mainWindow.timer.Start(int(1000.0/profile.niaFPS))
        
    def setIcon(self):
        ib = wx.IconBundle()
        if current.outputMode:
                bmp = self.make_grad_image(32,32, (255,255,0), (0,0,0))
                self.mainWindow.currentTopPanel.outputButton.SetLabel("Pause Output ( Ctrl F12 )")
        else:
                bmp = self.make_grad_image(32,32, (0,0,0), (0,0,0))
                self.mainWindow.currentTopPanel.outputButton.SetLabel("Continue Output ( Ctrl F11 )")
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(bmp)
        ib.AddIcon(icon)
        self.mainWindow.SetIcons(ib)
        
    def make_grad_image(self, width, height, col_left, col_right):
        array = numpy.zeros((height, width, 3), 'uint8')
        alpha = numpy.linspace(0.0, 1.0, width)
        color_gradient = numpy.outer(alpha, col_right) + \
               numpy.outer((1.0-alpha), col_left)
        array[:,:,:] = color_gradient
        image = wx.EmptyImage(width, height)
        image.SetData(array.tostring())
        return wx.BitmapFromImage(image)

if __name__ == "__main__":
    inputFaker = OutputManager.InputFaker()
    if inputFaker == -1:
        print "Import-Error: You need either SendKeys (Windows) or XLib (Linux, Mac)"
    else:
        profilefile = "" 
        keycodelistlabels = sorted(["Action: "+each for each in inputFaker.actions.keys()])
        if len(sys.argv)<2:
            path = os.getcwd()
            fileList = os.listdir(path)
            profileList = []
            for fileName in fileList:
                if fileName[-7:] == "profile":
                    profileList.append(fileName[:-8])
            if len(profileList) > 0:
                profilefile = str(WXElements.selection("Select your Profile",profileList[0], profileList))
            else:
                print "Error: no profiles found"
        else:
            profilefile = sys.argv[1]

        if len(profilefile)==0:
            print "Error: no profile name given.\nExample: python nia-Triathlon-Player.py myProfile"
        else:
            if len(profilefile)==0:
                profilefile = sys.argv[1] 
            profileLoaded = False
            netLoaded = False
            if os.path.exists(profilefile+".profile"):
                workfile = open(profilefile+".profile", "r")
                profile = pickle.load(workfile)
                workfile.close()
                profileLoaded = True
            else:
                print "no "+profilefile+".profile"+" file found"
            ann = libfann.neural_net()
            if os.path.exists(profilefile+".net"):
                ann.create_from_file(profilefile+".net")
                netLoaded = True
            else:
                print "no "+profilefile+".net"+" file found"
            if (profileLoaded and netLoaded):
                bciDevice =  InputManager.BCIDevice(profile.deviceName)
                current = Current_Data()
                argcp = ''
                glutInit(argcp, sys.argv)
                fannToOutputApp = FannToOutputApp()
                fannToOutputApp.MainLoop()
            else:
                print "Cannot start without .profile and .net files"
    
