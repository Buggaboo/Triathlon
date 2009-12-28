#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

# Howto, Code license, Credits, etc: http://code.google.com/B/BCI-Project-Triathlon/

noGL = False   # Set noGL to True for disabling the use of OpenGL (to gain speed, or to avoid python-wx-opengl problems)

import numpy
import wx
from mdp.nodes import PCANode
from mdp import Flow
import math
import threading
import random
import sys
import os
import pickle
from copy import deepcopy

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
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
    haveOpenGL = True
except ImportError:
    haveOpenGL = False
    noGL = True
    print "Will start without OpenGL, because PyOpenGL is not available."

class Collected_Data():
    def __init__(self):
        self.trainingMode = False
        self.currentReducedSample = []
        lenpcs = len(profile.channels)
        self.currentLabel = lenpcs*[0.0]
        self.dataClusters = lenpcs*[([],[])]

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

class InputCondition():
    def __init__(self,code=0,mouseButton=False,mouseMove=False,mouseMoveDir="up"):
        self.mouseButton = mouseButton
        self.mouseMove = mouseMove
        self.mouseMoveDir = mouseMoveDir
        self.code = code
        
    def isTrue(self,lastMousePos=(0,0), currentMousePos=(0,0)):
        if self.mouseButton:
            if self.code == 0:
                return wx.GetMouseState().leftDown
            elif self.code == 1:
                return wx.GetMouseState().rightDown
            else:
                return wx.GetMouseState().middleDown
        elif self.mouseMove:
            if self.mouseMoveDir == "up":
                return currentMousePos[1]-lastMousePos[1] < -2
            elif self.mouseMoveDir == "down":
                return currentMousePos[1]-lastMousePos[1] > 2
            elif self.mouseMoveDir == "left":
                return currentMousePos[0]-lastMousePos[0] < -2
            else:
                return currentMousePos[0]-lastMousePos[0] > 2
        else:
            return wx.GetKeyState(self.code)

inputConditions = {}
for each in "1234567890abcdefghijklmnopqrstuvwxyz":
    inputConditions[each] = InputCondition(code=ord(each))
    inputConditions["Arrow Left"] = InputCondition(code=wx.WXK_LEFT)
    inputConditions["Arrow Right"] = InputCondition(code=wx.WXK_RIGHT)
    inputConditions["Arrow Up"] = InputCondition(code=wx.WXK_UP)
    inputConditions["Arrow Down"] = InputCondition(code=wx.WXK_DOWN)
    inputConditions["F1"] = InputCondition(code=wx.WXK_F1)
    inputConditions["F2"] = InputCondition(code=wx.WXK_F2)
    inputConditions["F3"] = InputCondition(code=wx.WXK_F3)
    inputConditions["F4"] = InputCondition(code=wx.WXK_F4)
    inputConditions["F5"] = InputCondition(code=wx.WXK_F5)
    inputConditions["F6"] = InputCondition(code=wx.WXK_F6)
    inputConditions["F7"] = InputCondition(code=wx.WXK_F7)
    inputConditions["F8"] = InputCondition(code=wx.WXK_F8)
    inputConditions["F9"] = InputCondition(code=wx.WXK_F9)
    inputConditions["F10"] = InputCondition(code=wx.WXK_F10)
    inputConditions["F11"] = InputCondition(code=wx.WXK_F11)
    inputConditions["F12"] = InputCondition(code=wx.WXK_F12)
    inputConditions["Enter"] = InputCondition(code=wx.WXK_RETURN)
    inputConditions["Space"] = InputCondition(code=wx.WXK_SPACE)
    inputConditions["Backspace"] = InputCondition(code=wx.WXK_BACK)
    inputConditions["Page Up"] = InputCondition(code=wx.WXK_PAGEUP)
    inputConditions["Page Down"] = InputCondition(code=wx.WXK_PAGEDOWN)
    inputConditions["Home"] = InputCondition(code=wx.WXK_HOME)
    inputConditions["End"] = InputCondition(code=wx.WXK_END)
    inputConditions["Insert"] = InputCondition(code=wx.WXK_INSERT)
    inputConditions["Delete"] = InputCondition(code=wx.WXK_DELETE)
    inputConditions["Mouse Button Left"] = InputCondition(code=0,mouseButton=True)
    inputConditions["Mouse Button Right"] = InputCondition(code=1,mouseButton=True)
    inputConditions["Mouse Button Middle"] = InputCondition(code=2,mouseButton=True)
    inputConditions["Mouse Move Left"] = InputCondition(mouseMove=True,mouseMoveDir="left")
    inputConditions["Mouse Move Right"] = InputCondition(mouseMove=True,mouseMoveDir="right")
    inputConditions["Mouse Move Up"] = InputCondition(mouseMove=True,mouseMoveDir="up")
    inputConditions["Mouse Move Down"] = InputCondition(mouseMove=True,mouseMoveDir="down")

class AppSettings():
    def __init__(self,
                 availableChannels        = [OutputChannel('Strafe Left/Right',
                                                outputKeyList=[
                                                        ('Strafe Left','Arrow Left','Arrow Left'),
                                                        ('Strafe Right','Arrow Right','Arrow Right')]),
                                              OutputChannel('Move Forward/Backward',
                                                outputKeyList=[
                                                        ('Move Forward','Arrow Up','Arrow Up'),
                                                        ('Move Backward','Arrow Down','Arrow Down')]),
                                             OutputChannel('Jump / Crouch',allSamples = False,
                                                outputKeyList=[
                                                        ('Move Upwards','f','f'),
                                                        ('Move Downwards','c','c')]),
                                             OutputChannel('Primary / Secondary Fire',allSamples = False,
                                                outputKeyList=[
                                                        ('Primary Fire','Mouse Button Left','Mouse Button Left'),
                                                        ('Secondary Fire','Mouse Button Right','Mouse Button Right')]),
                                             OutputChannel('Mouse horizontal',allSamples = True,
                                                outputKeyList=[
                                                        ('Left','Mouse Move Left','Mouse Move Slow Left'),
                                                        ('Right','Mouse Move Right','Mouse Move Slow Right')]),
                                             OutputChannel('Mouse vertical',allSamples = True,
                                                outputKeyList=[
                                                        ('Left','Mouse Move Up','Mouse Move Slow Up'),
                                                        ('Right','Mouse Move Down','Mouse Move Slow Down')])],
                 dimensionReducerFlows = { 'None'    : 'Flow([])',
                                           'PCA  2D' : 'Flow([PCANode(output_dim=2)])',
                                           'PCA  4D' : 'Flow([PCANode(output_dim=4)])',
                                           'PCA  6D' : 'Flow([PCANode(output_dim=6)])',
                                           'PCA  8D' : 'Flow([PCANode(output_dim=8)])',
                                           'PCA 12D' : 'Flow([PCANode(output_dim=12)])',
                                           'PCA 16D' : 'Flow([PCANode(output_dim=16)])',
                                           'PCA 20D' : 'Flow([PCANode(output_dim=20)])',
                                           'PCA 25D' : 'Flow([PCANode(output_dim=25)])',
                                           'PCA 32D' : 'Flow([PCANode(output_dim=32)])',
                                           'PCA 45D' : 'Flow([PCANode(output_dim=45)])'}):
        self.availableChannels      = availableChannels
        self.dimensionReducerFlows  = dimensionReducerFlows
        self.showingTrainingPanel   = False
        self.tStage                 = 0
        self.flowTrainingChunck     = []

class ProfileSettings():
    def __init__(self,
                 freqRange              = (3,45),
                 timeTailLength         = 6,
                 niaFPS                 = 10,
                 flowTrainingChunckSize = 100,
                 trainingClusterSize    = 600,
                 testClusterSize        = 150,
                 profileName            = "myProfile",
                 dimensionReductionFlow = 'PCA 25D',
                 deviceName             = "OCZ Neural Impulse Actuator",
                 channels = [OutputChannel('Strafe Left/Right',
                                                outputKeyList=[
                                                        ('Strafe Left','Arrow Left','Arrow Left'),
                                                        ('Strafe Right','Arrow Right','Arrow Right')]),
                                              OutputChannel('Move Forward/Backward',
                                                outputKeyList=[
                                                        ('Move Forward','Arrow Up','Arrow Up'),
                                                        ('Move Backward','Arrow Down','Arrow Down')]),
                                             OutputChannel('Jump / Crouch',allSamples = False,
                                                outputKeyList=[
                                                        ('Move Upwards','f','f'),
                                                        ('Move Downwards','c','c')]),
                                             OutputChannel('Primary / Secondary Fire',allSamples = False,
                                                outputKeyList=[
                                                        ('Primary Fire','Mouse Button Left','Mouse Button Left'),
                                                        ('Secondary Fire','Mouse Button Right','Mouse Button Right')])]):
        self.freqRange              = freqRange
        self.timeTailLength         = timeTailLength
        self.niaFPS                 = niaFPS
        self.flowTrainingChunckSize = flowTrainingChunckSize
        self.trainingClusterSize    = trainingClusterSize
        self.testClusterSize        = testClusterSize
        self.profileName            = profileName
        self.dimensionReductionFlowLabel = dimensionReductionFlow
        self.dimensionReductionFlow = eval(settings.dimensionReducerFlows[dimensionReductionFlow])
        self.channels               = channels
        self.deviceName             = deviceName
        self.qfEnabled              = False
        self.qfAction               = 'p'
        self.qfThreshold            = 0.25

class ChannelPanel(wx.Panel):
    def __init__(self, parent,channelIndex):        
        wx.Panel.__init__(self, parent)
        self.channelIndex = channelIndex 
        panelSizer = wx.FlexGridSizer(0,4,0,0)
        self.channelCheckbox = wx.CheckBox(self,label='include in Profile')
        self.channelCheckbox.Bind(wx.EVT_CHECKBOX, self.includedChanged)
        if settings.availableChannels[channelIndex].channelName in [channel.channelName for channel in profile.channels]:
            self.channelCheckbox.SetValue(True)
        panelSizer.Add(self.channelCheckbox)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        self.channelAllSamplesCheckbox = wx.CheckBox(self,label='Max Samples')
        self.channelAllSamplesCheckbox.Bind(wx.EVT_CHECKBOX, self.allSamplesChanged)
        if settings.availableChannels[self.channelIndex].channelName in [channel.channelName for channel in profile.channels]:
            if  settings.availableChannels[self.channelIndex].allSamples:
                self.channelAllSamplesCheckbox.SetValue(True)
        panelSizer.Add(self.channelAllSamplesCheckbox)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(wx.StaticText(self,label=settings.availableChannels[channelIndex].outputKeyList[0][0]), 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        self.channelLowConditionChoice = wx.Choice(self,choices=inputConditionlistlabels)
        position = self.channelLowConditionChoice.FindString("Condition: "+settings.availableChannels[channelIndex].outputKeyList[0][1])
        self.channelLowConditionChoice.SetSelection(position)
        self.channelLowConditionChoice.Bind(wx.EVT_CHOICE, self.conditionChanged)
        panelSizer.Add(self.channelLowConditionChoice, 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(wx.StaticText(self,label=settings.availableChannels[channelIndex].outputKeyList[1][0]), 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        self.channelHighConditionChoice = wx.Choice(self,choices=inputConditionlistlabels)
        position = self.channelHighConditionChoice.FindString("Condition: "+settings.availableChannels[channelIndex].outputKeyList[1][1])
        self.channelHighConditionChoice.SetSelection(position)
        self.channelHighConditionChoice.Bind(wx.EVT_CHOICE, self.conditionChanged)
        panelSizer.Add(self.channelHighConditionChoice, 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        self.SetSizer(panelSizer)
        
    def includedChanged(self, event):
        self.GetGrandParent().channelsChanged()
        event.Skip()
        
    def allSamplesChanged(self, event):
        self.GetGrandParent().channelsChanged()
        event.Skip()
        
    def conditionChanged(self, event):
        self.GetGrandParent().channelsChanged()
        event.Skip()

class SettingPanel(wx.Panel):
    def __init__(self, parent):        
        wx.Panel.__init__(self, parent)
        acceptButton = wx.Button(self, id=-1, label='Use these settings')
        acceptButton.Bind(wx.EVT_BUTTON, self.Accept)
        panelSizer = wx.FlexGridSizer(0,1,0,0)
        namePanel = wx.Panel(self, wx.ID_ANY)
        nameSizer = wx.FlexGridSizer(1,0,0,0)
        nameSizer.Add(wx.StaticText(namePanel,label="Profile name:"), 0, wx.ALIGN_CENTER, 5)
        nameSizer.Add(wx.StaticText(namePanel,label=""), 0, wx.ALIGN_CENTER, 5)
        nameSizer.AddGrowableCol(2)
        self.nameField = wx.TextCtrl(namePanel,value=profile.profileName)
        self.nameField.Bind(wx.EVT_KILL_FOCUS, self.nameChanged)
        nameSizer.Add(self.nameField, 0, wx.EXPAND, 5)
        namePanel.SetSizer(nameSizer)
        flowTrainingSizePanel = wx.Panel(self, wx.ID_ANY)
        flowTrainingSizeSizer = wx.FlexGridSizer(1,0,0,0)
        flowTrainingSizeSizer.Add(wx.StaticText(flowTrainingSizePanel,label="Samples for flow-training:"), 0, wx.ALIGN_CENTER, 5)
        flowTrainingSizeSizer.AddGrowableCol(1)
        flowTrainingSizeSizer.Add(wx.StaticText(flowTrainingSizePanel,label=""), 0, wx.ALIGN_CENTER, 5)
        self.flowField = wx.TextCtrl(flowTrainingSizePanel,value=str(profile.flowTrainingChunckSize))
        self.flowField.Bind(wx.EVT_KILL_FOCUS, self.flowTrainSizeChanged)
        flowTrainingSizeSizer.Add(self.flowField)
        flowTrainingSizePanel.SetSizer(flowTrainingSizeSizer)
        clusterSizePanel = wx.Panel(self, wx.ID_ANY)
        clusterSizeSizer = wx.FlexGridSizer(1,0,0,0)
        clusterSizeSizer.Add(wx.StaticText(clusterSizePanel,label="Max Samples per training-cluster:"), 0, wx.ALIGN_CENTER, 5)
        clusterSizeSizer.AddGrowableCol(1)
        clusterSizeSizer.Add(wx.StaticText(clusterSizePanel,label=""), 0, wx.ALIGN_CENTER, 5)
        self.clusterField = wx.TextCtrl(clusterSizePanel,value=str(profile.trainingClusterSize))
        self.clusterField.Bind(wx.EVT_KILL_FOCUS, self.clusterSizeChanged)
        clusterSizeSizer.Add(self.clusterField)
        clusterSizePanel.SetSizer(clusterSizeSizer)
        testclusterSizePanel = wx.Panel(self, wx.ID_ANY)
        testclusterSizeSizer = wx.FlexGridSizer(1,0,0,0)
        testclusterSizeSizer.Add(wx.StaticText(testclusterSizePanel,label="Max Samples per test-cluster:"), 0, wx.ALIGN_CENTER, 5)
        testclusterSizeSizer.AddGrowableCol(1)
        testclusterSizeSizer.Add(wx.StaticText(testclusterSizePanel,label=""), 0, wx.ALIGN_CENTER, 5)
        self.testclusterField = wx.TextCtrl(testclusterSizePanel,value=str(profile.testClusterSize))
        self.testclusterField.Bind(wx.EVT_KILL_FOCUS, self.testSizeChanged)
        testclusterSizeSizer.Add(self.testclusterField)
        testclusterSizePanel.SetSizer(testclusterSizeSizer)
        freqRangePanel = wx.Panel(self, wx.ID_ANY)
        freqRangeSizer = wx.FlexGridSizer(1,0,0,0)
        freqRangeSizer.Add(wx.StaticText(freqRangePanel,label="Frequency range:"), 0, wx.ALIGN_CENTER, 5)
        freqRangeSizer.AddGrowableCol(1)
        freqRangeSizer.Add(wx.StaticText(freqRangePanel,label=""), 0, wx.ALIGN_CENTER, 5)
        self.fromFreqField = wx.TextCtrl(freqRangePanel,value=str(profile.freqRange[0]))
        self.fromFreqField.Bind(wx.EVT_KILL_FOCUS, self.freqChanged)
        freqRangeSizer.Add(self.fromFreqField)
        freqRangeSizer.Add(wx.StaticText(freqRangePanel,label=" - "), 0, wx.ALIGN_CENTER, 5)
        self.toFreqField = wx.TextCtrl(freqRangePanel,value=str(profile.freqRange[1]))
        self.toFreqField.Bind(wx.EVT_KILL_FOCUS, self.freqChanged)
        freqRangeSizer.Add(self.toFreqField)
        freqRangePanel.SetSizer(freqRangeSizer)
        tailLengthPanel = wx.Panel(self, wx.ID_ANY)
        tailLengthSizer = wx.FlexGridSizer(1,0,0,0)
        tailLengthSizer.Add(wx.StaticText(tailLengthPanel,label="Length of time-tail:"), 0, wx.ALIGN_CENTER, 5)
        tailLengthSizer.AddGrowableCol(1)
        tailLengthSizer.Add(wx.StaticText(tailLengthPanel,label=""), 0, wx.ALIGN_CENTER, 5)
        self.tailField = wx.TextCtrl(tailLengthPanel,value=str(profile.timeTailLength))
        self.tailField.Bind(wx.EVT_KILL_FOCUS, self.tailChanged)
        tailLengthSizer.Add(self.tailField)
        tailLengthPanel.SetSizer(tailLengthSizer)
        fpsPanel = wx.Panel(self, wx.ID_ANY)
        fpsSizer = wx.FlexGridSizer(1,0,0,0)
        fpsSizer.Add(wx.StaticText(fpsPanel,label="Samples per second:"), 0, wx.ALIGN_CENTER, 5)
        fpsSizer.AddGrowableCol(1)
        fpsSizer.Add(wx.StaticText(fpsPanel,label=""), 0, wx.ALIGN_CENTER, 5)
        self.fpsField = wx.TextCtrl(fpsPanel,value=str(profile.niaFPS))
        self.fpsField.Bind(wx.EVT_KILL_FOCUS, self.fpsChanged)
        fpsSizer.Add(self.fpsField)
        fpsPanel.SetSizer(fpsSizer)
        flowPanel = wx.Panel(self, wx.ID_ANY)
        flowSizer = wx.FlexGridSizer(1,0,0,0)
        flowSizer.Add(wx.StaticText(flowPanel,label="Dimension-reduction Flow:"), 0, wx.ALIGN_CENTER, 5)
        flowSizer.AddGrowableCol(1)
        flowSizer.Add(wx.StaticText(flowPanel,label=""), 0, wx.ALIGN_CENTER, 5)
        self.flowChoice = wx.Choice(flowPanel,choices=sorted(settings.dimensionReducerFlows.keys()))
        position = self.flowChoice.FindString(profile.dimensionReductionFlowLabel)
        self.flowChoice.SetSelection (position)
        flowSizer.Add(self.flowChoice)
        flowPanel.SetSizer(flowSizer)
        qfPanel = wx.Panel(self, wx.ID_ANY)
        qfSizer = wx.FlexGridSizer(1,0,0,0)
        self.qfCheckbox = wx.CheckBox(qfPanel,label='Quickfire in training')
        self.qfCheckbox.SetValue(profile.qfEnabled)
        self.qfCheckbox.Bind(wx.EVT_CHECKBOX, self.qfChanged)
        qfSizer.Add(self.qfCheckbox, 0, wx.ALIGN_CENTER, 5)
        qfSizer.AddGrowableCol(1)
        self.qfActionChoice = wx.Choice(qfPanel, choices=keycodelistlabels)
        position = self.qfActionChoice.FindString("Action: "+profile.qfAction)            
        self.qfActionChoice.SetSelection (position)        
        self.qfActionChoice.Bind(wx.EVT_CHOICE, self.qfActioncodeChanged)
        qfSizer.Add(self.qfActionChoice, 0, wx.ALIGN_RIGHT, 5)
        qfPanel.SetSizer(qfSizer)
        channelsNotebook = wx.Notebook(self)
        self.channelPannels = []
        for channelIndex in xrange(len(settings.availableChannels)):
            self.channelPannels.append(ChannelPanel(channelsNotebook,channelIndex))
            channelsNotebook.AddPage(self.channelPannels[channelIndex], settings.availableChannels[channelIndex].channelName)
        panelSizer.AddGrowableCol(0)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(namePanel, 0, wx.EXPAND, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.EXPAND, 5)
        panelSizer.Add(channelsNotebook, 0, wx.EXPAND, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.EXPAND, 5)
        panelSizer.Add(flowTrainingSizePanel, 0, wx.EXPAND, 5)
        panelSizer.Add(clusterSizePanel, 0, wx.EXPAND, 5)
        panelSizer.Add(testclusterSizePanel, 0, wx.EXPAND, 5)
        panelSizer.Add(freqRangePanel, 0, wx.EXPAND, 5)
        panelSizer.Add(tailLengthPanel, 0, wx.EXPAND, 5)
        panelSizer.Add(fpsPanel, 0, wx.EXPAND, 5)
        panelSizer.Add(flowPanel, 0, wx.EXPAND, 5)
        panelSizer.Add(qfPanel, 0, wx.EXPAND, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.EXPAND, 5)
        panelSizer.Add(acceptButton, 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        self.SetSizer(panelSizer)
        self.SetAutoLayout(1)
        
    def Accept(self, event):
        label = self.flowChoice.GetStringSelection()
        profile.dimensionReductionFlowLabel = label
        profile.dimensionReductionFlow = eval(settings.dimensionReducerFlows[label])
        lenpcs = len(profile.channels)
        collected.currentLabel = lenpcs*[0.0]
        collected.dataClusters = lenpcs*[([],[])]
        self.GetGrandParent().GetParent().enterTraining()
        event.Skip()
        
    def tailChanged(self, event):
        val = 0
        try:
                val = int(self.tailField.GetValue())
        except ValueError:
                val = profile.timeTailLength
        if (val<0):
                val = 0
        elif (val>20):
                val = 20
        profile.timeTailLength = val
        self.tailField.SetValue(str(val))
        self.GetGrandParent().GetParent().visualizationPanel.resetReading()
        event.Skip()
        
    def fpsChanged(self, event):
        val = 0
        try:
                val = int(self.fpsField.GetValue())
        except ValueError:
                val = profile.niaFPS
        if (val<1):
                val = 1
        elif (val>50):
                val = 50
        profile.niaFPS = val
        self.fpsField.SetValue(str(val))
        self.GetGrandParent().GetParent().timer.Stop()
        bciDevice.setPoints(int(500.0/profile.niaFPS))
        self.GetGrandParent().GetParent().timer.Start(int(1000.0/profile.niaFPS))
        self.GetGrandParent().GetParent().visualizationPanel.resetReading()
        event.Skip()
        
    def freqChanged(self, event):
        fr = 0
        try:
                fr = int(self.fromFreqField.GetValue())
        except ValueError:
                fr = profile.freqRange[0]
        if (fr<0):
                fr = 0
        elif (fr>100):
                fr = 100
        to = 0
        try:
                to = int(self.toFreqField.GetValue())
        except ValueError:
                to = profile.freqRange[1]
        if (to<0):
                to = 0
        elif (to>100):
                to = 100
        if to<fr:
            sw = fr
            fr = to
            to = sw
        elif to == fr:
            to = to+2
        if abs(to-fr)==1:
            to=to+1
        self.fromFreqField.SetValue(str(fr))
        self.toFreqField.SetValue(str(to))
        profile.freqRange = (fr,to)
        self.GetGrandParent().GetParent().visualizationPanel.resetReading()
        event.Skip()
        
    def flowTrainSizeChanged(self, event):
        si = 0
        try:
                si = int(self.flowField.GetValue())
        except ValueError:
                si = profile.flowTrainingChunckSize
        if si<=0:
                si = 100
        profile.flowTrainingChunckSize = si
        self.flowField.SetValue(str(si))
        event.Skip()
        
    def clusterSizeChanged(self, event):
        si = 0
        try:
                si = int(self.clusterField.GetValue())
        except ValueError:
                si = profile.trainingClusterSize
        if si<=0:
                si = 200
        profile.trainingClusterSize = si
        self.clusterField.SetValue(str(si))
        event.Skip()
        
    def testSizeChanged(self, event):
        si = 0
        try:
                si = int(self.testclusterField.GetValue())
        except ValueError:
                si = profile.testClusterSize
        if si<=0:
                si = 200
        profile.testClusterSize = si
        self.testclusterField.SetValue(str(si))
        event.Skip()
        
    def nameChanged(self, event):
        if (self.nameField.GetValue()!=''):
                profile.profileName = self.nameField.GetValue()
        else:
                self.nameField.SetValue(profile.profileName)
        event.Skip()
        
    def channelsChanged(self):    
        newChannels=[]
        atLeastOne=False
        atLeastOneAllSamples=False
        for avChannelIndex in range(len(settings.availableChannels)):
            if  self.channelPannels[avChannelIndex].channelCheckbox.IsChecked():
                atLeastOne=True
                newChannels.append(deepcopy(settings.availableChannels[avChannelIndex]))
                if self.channelPannels[avChannelIndex].channelAllSamplesCheckbox.IsChecked():
                    atLeastOneAllSamples=True
                    newChannels[-1].allSamples = True
                else:
                    newChannels[-1].allSamples = False
                newChannels[-1].outputKeyList[0] = (newChannels[-1].outputKeyList[0][0],
                                                    self.channelPannels[avChannelIndex].channelLowConditionChoice.GetStringSelection()[11:],
                                                    newChannels[-1].outputKeyList[0][2])
                newChannels[-1].outputKeyList[1] = (newChannels[-1].outputKeyList[1][0],
                                                    self.channelPannels[avChannelIndex].channelHighConditionChoice.GetStringSelection()[11:],
                                                    newChannels[-1].outputKeyList[1][2])
        if not atLeastOne:
            self.channelPannels[0].channelCheckbox.SetValue(True)
            newChannels.append(settings.availableChannels[0])
            self.channelPannels[0].channelAllSamplesCheckbox.SetValue(True)
            settings.availableChannels[0].allSamples = True
            newChannels[-1].allSamples = True
            newChannels[-1].outputKeyList[0] = (newChannels[-1].outputKeyList[0][0],
                                                self.channelPannels[avChannelIndex].channelLowConditionChoice.GetStringSelection()[11:],
                                                newChannels[-1].outputKeyList[0][2])
            newChannels[-1].outputKeyList[1] = (newChannels[-1].outputKeyList[1][0],
                                                self.channelPannels[avChannelIndex].channelHighConditionChoice.GetStringSelection()[11:],
                                                newChannels[-1].outputKeyList[1][2])
            atLeastOneAllSamples = True
        if not atLeastOneAllSamples:
            firstI = -1
            for index in range(len(settings.availableChannels)):
                if self.channelPannels[index].channelCheckbox.IsChecked():
                    firstI = index
                    break
            settings.availableChannels[firstI].allSamples = True
            self.channelPannels[firstI].channelAllSamplesCheckbox.SetValue(True)
            newChannels[0].allSamples = True
        profile.channels = newChannels
        self.GetGrandParent().GetParent().visualizationPanel.resetReading()
        
    def qfChanged(self, event):
        profile.qfEnabled = self.qfCheckbox.IsChecked()
        event.Skip()
        
    def qfActioncodeChanged(self, event):
        profile.qfAction = self.qfActionChoice.GetStringSelection()[8:]
        event.Skip()

class VisualizationPanel(WXElements.GLCanvasBase):
   def InitGL(self):
       self.maxScaler = 30.0
       self.spacer = 0.02
       self.field = 0.16
       self.ylists = [ bciDevice.frequenciesCombined(profile.freqRange[0],profile.freqRange[1])
                       for each in xrange(profile.timeTailLength+1)]
       self.raw = [[1.0,1.0,1.0] for each in xrange(50)]
       self.xlist = [float(i)/float(-1+len(self.ylists[0])) for i in xrange(len(self.ylists[0]))]
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
       if (settings.tStage==3):
           glColor(1.0,1.0,0.0)  
           wave_array = [ [math.cos(float(i)*2*math.pi/len(collected.currentReducedSample))* (0.2+(collected.currentReducedSample[i]/self.maxScaler)),
                                  math.sin(float(i)*2*math.pi/len(collected.currentReducedSample))* (0.2+(collected.currentReducedSample[i]/self.maxScaler))]
                                for i in range(len(collected.currentReducedSample))]
           wave_array.append(wave_array[0])
           glVertexPointerf(wave_array)
           glDrawArrays(GL_LINE_STRIP, 0, len(wave_array))
           glColor(0.0,0.8,0.0)
           for channelIndex in range(len(collected.currentLabel)):
                centerL = ( -1.0 + ((self.spacer * 4.0 )+(self.field * 3.0 ) ),
                             1.0 - ((self.spacer * (1.0+float(channelIndex)) )+(self.field * (0.5+float(channelIndex)) )))
                t = float(len(collected.dataClusters[channelIndex][0])+len(collected.dataClusters[channelIndex][1])) / float(
                        2*(profile.testClusterSize+profile.trainingClusterSize))
                glVertexPointerf([
                        [centerL[0] ,centerL[1] + (0.5 * self.field)],
                        [centerL[0] ,centerL[1] - (0.5 * self.field)],
                        [centerL[0] + (t * ((1.0-self.spacer)- centerL[0])),centerL[1] + (0.5 * self.field)],
                        [centerL[0] + (t * ((1.0-self.spacer)- centerL[0])),centerL[1] - (0.5 * self.field)]])
                glDrawArrays(GL_QUAD_STRIP, 0, 4)
       else:
         for historyIndex in reversed(xrange(profile.timeTailLength+1)):
           glColor(0.7*(float(historyIndex)/float(profile.timeTailLength+1)),0.7-0.6*(float(historyIndex)/float(profile.timeTailLength+1)),0.0)
           wave_array = [ [math.cos(float(i)*2*math.pi/len(self.xlist))* ((0.8-(0.04*historyIndex))+(10.0*self.ylists[historyIndex][i]/self.maxScaler)),
                                  math.sin(float(i)*2*math.pi/len(self.xlist))* ((0.8-(0.04*historyIndex))+(10.0*self.ylists[historyIndex][i]/self.maxScaler))]
                                for i in xrange(len(self.xlist))]
           wave_array.append(wave_array[0])
           glVertexPointerf(wave_array)
           glDrawArrays(GL_LINE_STRIP, 0, len(wave_array))
       for channelIndex in range(len(collected.currentLabel)):
           for i in range(3):
                if (int(collected.currentLabel[channelIndex])+1==i):
                    if profile.channels[-len(profile.channels) + channelIndex].allSamples:
                        glColor(0.6,0.3,0.8)
                    else:
                        glColor(0.3,0.3,1.3)
                else:
                    glColor(0.3,0.3,0.3)
                center = ( -1.0 + ((self.spacer * (1.0+float(i)) )+(self.field * (0.5+float(i)) ) ),
                            1.0 - ((self.spacer * (1.0+float(channelIndex)) )+(self.field * (0.5+float(channelIndex)) )))
                glVertexPointerf([
                        [center[0] + (0.5 * self.field),center[1] + (0.5 * self.field)],
                        [center[0] + (0.5 * self.field),center[1] - (0.5 * self.field)],
                        [center[0] - (0.5 * self.field),center[1] + (0.5 * self.field)],
                        [center[0] - (0.5 * self.field),center[1] - (0.5 * self.field)]])
                glDrawArrays(GL_QUAD_STRIP, 0, 4)
           glColor(0.85,0.85,0.85)
           glRasterPos2f(-1.0 + ((self.spacer * 5.0 )+(self.field * 3.0 ) ),
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
        self.ylists = [bciDevice.frequenciesCombined(profile.freqRange[0],profile.freqRange[1])]+self.ylists[0:profile.timeTailLength]
        self.raw = [ [ float(min(bciDevice.working_Data(0)[-385:-1]))/ float(bciDevice.calibration(0)), 
                     float(max(bciDevice.working_Data(0)[-385:-1]))/ float(bciDevice.calibration(0)),
                     float(sum(bciDevice.working_Data(0)[-385:-1])/385)/ float(bciDevice.calibration(0))] ]+self.raw[0:49]
        if self.GetParent().IsShown():
            self.SetCurrent()
            self.OnDraw()
            
   def resetReading(self):
        self.ylists = [ bciDevice.frequenciesCombined(profile.freqRange[0],profile.freqRange[1])
                       for each in xrange(profile.timeTailLength+1)]
        self.xlist = [float(i)/float(-1+len(self.ylists[0])) for i in xrange(len(self.ylists[0]))]
        self.raw = [[1.0,1.0,1.0] for each in xrange(50)]
        if self.GetParent().IsShown():
            self.SetCurrent()
            self.OnDraw()
        
class ResultPanel(wx.Panel):
    def __init__(self, parent):        
        wx.Panel.__init__(self, parent)
        cancelButton = wx.Button(self, id=-1, label='Cancel')
        cancelButton.Bind(wx.EVT_BUTTON, self.Cancel)
        self.channelPanels=[]
        for channelIndex in range(len(settings.availableChannels)):
                self.channelPanels.append(ResultChannelPanel(self,settings.availableChannels[channelIndex].channelName))
        panelSizer = wx.FlexGridSizer(0,1,0,0)
        panelSizer.AddGrowableCol(0)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        self.playPauseButton = wx.Button(self,label="      Start Training ( Ctrl F11 )      ")
        self.playPauseButton.Bind(wx.EVT_BUTTON, self.trainingModeSwitching)
        panelSizer.Add(self.playPauseButton, 0, wx.EXPAND, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        self.flowText = wx.StaticText(self,label="Flow Training:")
        panelSizer.Add(self.flowText, 0, wx.EXPAND, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        for channelIndex in xrange(len(settings.availableChannels)):
                panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
                panelSizer.Add(self.channelPanels[channelIndex], 0, wx.EXPAND, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(cancelButton, 0, wx.ALIGN_CENTER, 5)
        panelSizer.Add(wx.StaticText(self,label=" "), 0, wx.ALIGN_CENTER, 5)
        self.SetSizer(panelSizer)
        self.SetAutoLayout(1)
        
    def Cancel(self, event):
        self.GetGrandParent().GetParent().cancelTraining()
        event.Skip()
        
    def trainingModeSwitching(self, event):
        if collected.trainingMode:
                collected.trainingMode=False
        else:
                collected.trainingMode=True
                bciDevice.calibrateAll()
        niatofannApp.setIcon()
        event.Skip()
        
    def reset(self):
        self.playPauseButton.SetLabel("      Start Training ( Ctrl F11 )      ")
        self.flowText.SetLabel("Flow Training:")
        for channelIndex in range(len(settings.availableChannels)):
            self.channelPanels[channelIndex].text.SetLabel("")

class ResultChannelPanel(wx.Panel):
    def __init__(self, parent,chlabel):        
        wx.Panel.__init__(self, parent)
        self.text = wx.StaticText(self, label='')
        self.channelname = wx.StaticText(self, label=(chlabel+": "))
        panelSizer = wx.FlexGridSizer(0,1,0,0)
        panelSizer.AddGrowableRow(0)
        panelSizer.Add(self.channelname, 0, wx.EXPAND, 5)
        panelSizer.AddGrowableCol(1)
        panelSizer.Add(self.text, 0, wx.EXPAND, 5)
        self.SetSizer(panelSizer)
        self.SetAutoLayout(1)

class GUIMain(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,None,title="Triathlon Auditor",size=(800,560))
        self.panel = wx.Panel(self, wx.ID_ANY)
        MenuBar = wx.MenuBar()
        self.FileMenu = wx.Menu()
        item = self.FileMenu.Append(wx.ID_ANY, text="Calibrate")
        self.Bind(wx.EVT_MENU, self.OnCalibrate, item)
        item = self.FileMenu.Append(wx.ID_EXIT, text="Quit")
        self.Bind(wx.EVT_MENU, self.OnQuit, item)
        MenuBar.Append(self.FileMenu, "Menu")
        self.SetMenuBar(MenuBar)
        self.stageNotebook = wx.Notebook(self.panel)
        self.settingPanel = SettingPanel(self.stageNotebook)
        self.resultPanel = ResultPanel(self.stageNotebook)
        self.visualizationPanel = ''
        if noGL:
            self.visualizationPanel = WXElements.NoGLVisualizationPanel(self.panel)
        else: 
            self.visualizationPanel = VisualizationPanel(self.panel)
        sizer = wx.FlexGridSizer(1,3,0,0)
        self.stageNotebook.AddPage(self.settingPanel,"Settings")
        self.stageNotebook.AddPage(self.resultPanel,"Training")
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.NotebookChanged, self.stageNotebook)
        sizer.AddGrowableRow(0)
        sizer.Add(self.stageNotebook , 1, wx.EXPAND)
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
        self.currentReducedLabeledSample = ([],[])

        self.timer = wx.Timer(self, wx.ID_ANY)
        self.Bind(wx.EVT_TIMER, self.NiaUpdate, self.timer)
        self.oldMousePos = (wx.GetMouseState().GetX(),wx.GetMouseState().GetY())
        
    def OnQuit(self, event):
        self.timer.Stop()
        self.Close()
        
    def OnCalibrate(self, event):
        bciDevice.calibrateAll()
        event.Skip()
        
    def qfChanged(self, event):
        profile.qfThreshold = (float(30+self.qfThresholdSlider.GetValue())/1060.0)
        event.Skip()
        
    def enterTraining(self):
        settings.showingTrainingPanel = True
        settings.tStage = 1
        self.resultPanel.reset()
        self.stageNotebook.SetSelection(1)
        
    def cancelTraining(self):
        settings.showingTrainingPanel = False
        settings.tStage = 0
        settings.flowTrainingChunck = []
        self.stageNotebook.SetSelection(0)
        collected.trainingMode=False
        niatofannApp.setIcon()
        collected.currentReducedSample =[]
        collected.dataClusters = [([],[]) for each in profile.channels]
        
    def NotebookChanged(self, event):
        if settings.tStage == 0:
            if self.stageNotebook.GetSelection() != 0:
                self.stageNotebook.SetSelection(0)
        else:
            if self.stageNotebook.GetSelection() != 1:
                self.stageNotebook.SetSelection(1)
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
        curLabel=[]
        mousePos = (wx.GetMouseState().GetX(),wx.GetMouseState().GetY())
        for channel in profile.channels:
            if inputConditions[channel.outputKeyList[0][1]].isTrue(lastMousePos=self.oldMousePos, currentMousePos=mousePos):
                curLabel.append(-1.0)
            elif inputConditions[channel.outputKeyList[1][1]].isTrue(lastMousePos=self.oldMousePos, currentMousePos=mousePos):
                curLabel.append(1.0)
            else:
                curLabel.append(0.0)
        self.oldMousePos = mousePos
        collected.currentLabel = curLabel
        if (wx.GetKeyState(wx.WXK_CONTROL) and wx.GetKeyState(wx.WXK_F12)): 
            if collected.trainingMode:                                    # switch training-mode off
                collected.trainingMode=False
                niatofannApp.setIcon()
        elif (wx.GetKeyState(wx.WXK_CONTROL) and wx.GetKeyState(wx.WXK_F11)):
            if (not(collected.trainingMode) and settings.showingTrainingPanel): # switch training-mode on
                collected.trainingMode=True
                niatofannApp.setIcon()
                bciDevice.calibrateAll()
        sample=[]
        [sample.extend(i) for i in self.currentReadingsAndTail]
        wait=False
        if ((settings.tStage == 1) and collected.trainingMode): # collecting dimension-reduction-Flow-training chunck
          if (random.random()<0.2):
            settings.flowTrainingChunck.append(sample)
            self.resultPanel.flowText.SetLabel(''.join(["Flow Training:\n", \
              str(len(settings.flowTrainingChunck))," of ",                                                                str(profile.flowTrainingChunckSize)," Samples"]))
            if len(settings.flowTrainingChunck)==profile.flowTrainingChunckSize: # train dimension-reduction-Flow
                settings.tStage = 2
                if profile.dimensionReductionFlowLabel!="None":
                        profile.dimensionReductionFlow.train(numpy.array(settings.flowTrainingChunck))
                settings.flowTrainingChunck=[]
                settings.tStage = 3
                wait=True
                for channelIndex in range(len(profile.channels)):
                    allIndex = 0
                    for allInd in range(len(settings.availableChannels)):
                      if profile.channels[channelIndex].channelName == settings.availableChannels[allInd].channelName:
                          allIndex = allInd
                          break
                    if profile.channels[channelIndex].allSamples:
                        self.resultPanel.channelPanels[allIndex].text.SetLabel(
                            '0 of '+str((profile.testClusterSize+profile.trainingClusterSize)*2)+' Samples')
                    else:
                        self.resultPanel.channelPanels[allIndex].text.SetLabel('0 Samples')
        elif ((settings.tStage == 3) and collected.trainingMode): # collect labeled dim-reduced feature samples
            wait=False
            if profile.dimensionReductionFlowLabel=="None":
                    collected.currentReducedSample = sample
            else:
                    collected.currentReducedSample = profile.dimensionReductionFlow(numpy.array([sample]))[0]
            self.currentReducedLabeledSample = (collected.currentReducedSample  , collected.currentLabel)
            if sum([abs(each) for each in collected.currentLabel])!=0.0: # (only if there is input at all right now)
                for channelIndex in range(len(profile.channels)):
                  allIndex = 0
                  for allInd in range(len(settings.availableChannels)):
                      if profile.channels[channelIndex].channelName == settings.availableChannels[allInd].channelName:
                          allIndex = allInd
                          break
                  if random.random()<(float(channelIndex+1)/float(len(profile.channels))):
                    if ((collected.currentLabel[channelIndex]==-1.0) 
                        and (len(collected.dataClusters[channelIndex][0])<(profile.trainingClusterSize+profile.testClusterSize))):
                        collected.dataClusters[channelIndex][0].append(self.currentReducedLabeledSample)
                        if  profile.channels[channelIndex].allSamples:
                            self.resultPanel.channelPanels[allIndex].text.SetLabel(
                                        str(len(collected.dataClusters[channelIndex][0])+len(collected.dataClusters[channelIndex][1]))+
                                        ' of '+
                                        str(2*(profile.testClusterSize+profile.trainingClusterSize))+
                                        ' Samples'                                        
                                        )
                        else:
                            self.resultPanel.channelPanels[allIndex].text.SetLabel(
                                        str(len(collected.dataClusters[channelIndex][0])+len(collected.dataClusters[channelIndex][1]))+
                                        ' Samples'                                        
                                        )
                        break
                    elif ((collected.currentLabel[channelIndex]==1.0) 
                          and (len(collected.dataClusters[channelIndex][1])<(profile.trainingClusterSize+profile.testClusterSize))):
                        collected.dataClusters[channelIndex][1].append(self.currentReducedLabeledSample)
                        if  profile.channels[channelIndex].allSamples:
                            self.resultPanel.channelPanels[allIndex].text.SetLabel(
                                        str(len(collected.dataClusters[channelIndex][0])+len(collected.dataClusters[channelIndex][1]))+
                                        ' of '+
                                        str(2*(profile.testClusterSize+profile.trainingClusterSize))+
                                        ' Samples'                                        
                                        )
                        else:
                            self.resultPanel.channelPanels[allIndex].text.SetLabel(
                                        str(len(collected.dataClusters[channelIndex][0])+len(collected.dataClusters[channelIndex][1]))+
                                        ' Samples'                                        
                                        )
                        break
                sofarOfRequired = 0
                for eachI in range(len(profile.channels)):
                    if profile.channels[eachI].allSamples:
                        sofarOfRequired += len(collected.dataClusters[eachI][0])+len(collected.dataClusters[eachI][1])
                required = (profile.testClusterSize+profile.trainingClusterSize)*2*len(filter(lambda a:a.allSamples,profile.channels))
                if (sofarOfRequired == required):
                    settings.tStage = 4
                    if os.path.exists(profile.profileName+".profile"):
                            os.remove(profile.profileName+".profile")
                    workfile = open(profile.profileName+".profile", "w")
                    pickle.dump(profile, workfile)
                    workfile.close()
                    if os.path.exists(profile.profileName+".train"):
                            os.remove(profile.profileName+".train")
                    if os.path.exists(profile.profileName+".test"):
                            os.remove(profile.profileName+".test")
                    finalListOfAllSamples = []
                    finalListOfTestSamples =[]
                    for channelIndex in range(len(collected.dataClusters)):
                        random.shuffle(collected.dataClusters[channelIndex][0])
                        random.shuffle(collected.dataClusters[channelIndex][1])
                        if profile.channels[channelIndex].allSamples:
                            finalListOfAllSamples.extend(collected.dataClusters[channelIndex][0][:profile.trainingClusterSize])
                            finalListOfAllSamples.extend(collected.dataClusters[channelIndex][1][:profile.trainingClusterSize])
                            finalListOfTestSamples.extend(collected.dataClusters[channelIndex][0][profile.trainingClusterSize:])
                            finalListOfTestSamples.extend(collected.dataClusters[channelIndex][1][profile.trainingClusterSize:])
                        else:
                            ratio = float(profile.testClusterSize) / float(profile.trainingClusterSize)
                            cutIndex = int(round( ratio * len(collected.dataClusters[channelIndex][0])))
                            finalListOfAllSamples.extend(collected.dataClusters[channelIndex][0][cutIndex:])
                            finalListOfTestSamples.extend(collected.dataClusters[channelIndex][0][:cutIndex])
                            cutIndex = int(round( ratio * len(collected.dataClusters[channelIndex][1])))
                            finalListOfTestSamples.extend(collected.dataClusters[channelIndex][1][:cutIndex])  
                            finalListOfAllSamples.extend(collected.dataClusters[channelIndex][1][cutIndex:])
                    random.shuffle(finalListOfAllSamples)
                    random.shuffle(finalListOfTestSamples)
                    workfile = open(profile.profileName+".train", "w")
                    workfile2 = open(profile.profileName+".test", "w")
                    workfile.write(     ' '.join([str(len(finalListOfAllSamples)),
                                        str(len(collected.dataClusters[0][0][0][0])),
                                        str(len(profile.channels)),'\n']))
                    workfile2.write(    ' '.join([str(len(finalListOfTestSamples)),
                                        str(len(collected.dataClusters[0][0][0][0])),
                                        str(len(profile.channels)),'\n']))
                    for labledSample in finalListOfAllSamples:
                        workfile.write(" ".join(map(lambda x: str(x).replace(",","."), labledSample[0])) , "\n" ,
                                       " ".join(map(lambda x: str(x).replace(",","."), labledSample[1])) + "\n")
                    for labledSample in finalListOfTestSamples:
                        workfile2.write(" ".join(map(lambda x: str(x).replace(",","."), labledSample[0])) + "\n" + 
                                        " ".join(map(lambda x: str(x).replace(",","."), labledSample[1])) + "\n")
                    workfile.close()
                    workfile2.close()
                    self.cancelTraining()
                    suc = wx.MessageDialog(self,
                      ''.join([
                                "Saved as:\n\n",
                                profile.profileName,".profile\n",
                                profile.profileName,".train\n",
                                profile.profileName,".test",
                                "\n\nYou can close this application now\n",
                                "and proceed with the Breeder"])
                      , "Finished", wx.OK)
                    suc.ShowModal()
                    suc.Destroy()
        if ((settings.tStage >= 1) and collected.trainingMode and profile.qfEnabled): # Quickfire
                if (profile.qfThreshold*2.0) <= (float(sum(bciDevice.working_Data(0)[-385:-1])/385)/ float(bciDevice.calibration(0)
                                                )*(float(max(bciDevice.working_Data(0)[-385:-1]))/ float(bciDevice.calibration(0)
                                                )-float(min(bciDevice.working_Data(0)[-385:-1]))/ float(bciDevice.calibration(0)))):
                        inputFaker.keyHold(profile.qfAction)
                else:
                        inputFaker.keyRelease(profile.qfAction)
                inputFaker.flush()
        if not(wait):
            self.visualizationPanel.newReading()
        ev.Skip()

class NiatofannApp(wx.App):
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
        if collected.trainingMode:
                bmp = self.make_grad_image(32,32, (0,255,0), (0,0,0))
        else:
                bmp = self.make_grad_image(32,32, (0,0,0), (0,0,0))
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(bmp)
        ib.AddIcon(icon)
        self.mainWindow.SetIcons(ib)
        if settings.showingTrainingPanel:
            if collected.trainingMode:
                self.mainWindow.resultPanel.playPauseButton.SetLabel("    Pause Training ( Ctrl F12 )    ")
            else:
                self.mainWindow.resultPanel.playPauseButton.SetLabel(" Continue Training ( Ctrl F11 ) ")
                
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
        keycodelistlabels = sorted(["Action: "+each for each in inputFaker.actions.keys()])
        inputConditionlistlabels = sorted(["Condition: "+each for each in inputConditions.keys()])
        settings = AppSettings()
        profile = ProfileSettings()
        if len(sys.argv)==2:
            profilefile = sys.argv[1]
            if os.path.exists(profilefile+".profile"):
                workfile = open(profilefile+".profile", "r")
                profile = pickle.load(workfile)
                workfile.close()
            else:
                print ''.join(["no ",profilefile, ".profile file found"])
        else:
            selection = WXElements.selection("Select your Device",InputManager.SupportedDevices.keys()[0],InputManager.SupportedDevices.keys())
            profile.deviceName = selection
        bciDevice =  InputManager.BCIDevice(profile.deviceName)
        collected = Collected_Data()
        argcp = ''
        glutInit(argcp, sys.argv)
        niatofannApp = NiatofannApp()
        niatofannApp.MainLoop()
