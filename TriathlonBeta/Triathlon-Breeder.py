#!/usr/bin/python

# Howto, Code license, Credits, etc: http://code.google.com/B/BCI-Project-Triathlon/

noGL = False   # Set noGL to True for disabling the use of OpenGL (to gain speed, or to avoid python-wx-opengl problems)


import pyfann
from pyfann import libfann
import string
import os
import sys
import random
import copy
import wx
import numpy
from array import array

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

class AppSettings():
    def __init__(self,
                 datafile,
                 desired_error = 0.0000000001,
                 iterations_between_reports = 1000):
        self.datafile = datafile
        self.desired_error = desired_error
        self.iterations_between_reports  = iterations_between_reports
        f = open(datafile+".train", 'r')
        firstline = f.readline()
        f.close
        l = string.split(firstline)
        self.num_input = int(l[1])
        self.num_output = int(l[2])
        self.breeding = False
        self.stage = 0
        self.netsTried = 0
        self.maxMutations = 18
        self.populationSize = 12
        self.trainingData = libfann.training_data()
        self.trainingData.read_train_from_file(datafile+".train")
        self.testData = libfann.training_data()
        self.testData.read_train_from_file(datafile+".test")
        self.flist = [libfann.FANN_LINEAR,libfann.FANN_SIGMOID,libfann.FANN_SIGMOID_STEPWISE,libfann.FANN_SIGMOID_SYMMETRIC,libfann.FANN_SIGMOID_SYMMETRIC_STEPWISE,
                      libfann.FANN_GAUSSIAN,libfann.FANN_GAUSSIAN_SYMMETRIC,libfann.FANN_ELLIOT,libfann.FANN_ELLIOT_SYMMETRIC,libfann.FANN_LINEAR_PIECE,
                      libfann.FANN_LINEAR_PIECE_SYMMETRIC,libfann.FANN_SIN_SYMMETRIC,libfann.FANN_COS_SYMMETRIC]
        self.mutationlist = ["change_connection_rate",
                        "change_learning_rate",
                        "change_num_neurons_hidden",
                        "change_num_layers_hidden",
                        "change_max_iterations",
                        "change_training_algorithm",
                        "change_activation_function_hidden",
                        "change_activation_function_output",
                        "change_learning_momentum",
                        "change_activation_steepness_hidden",
                        "change_activation_steepness_output",
                        "change_training_param"]
        self.trmutlist = ["change_connection_type",
                          "change_quickprop_decay",
                          "change_quickprop_mu",
                          "change_rprop_increase_factor",
                          "change_rprop_decrease_factor",
                          "change_rprop_delta_min",
                          "change_rprop_delta_max",
#                          "change_rprop_delta_zero"
                           ]

class BreedingEventTimer(wx.Timer):
    def __init__(self):
        wx.Timer.__init__(self)
        self.population = NeuralNetPopulation(maxSize=settings.populationSize)
        self.childNN = ""
        self.Start(20)
    def Notify(self):
        if settings.breeding:
            self.evolve(1)
    def evolve(self,steps):
        if settings.breeding:
          for i in range(steps):
            newStage = 0
            if settings.stage == 0:
                names = ["Adam","Eve","Joe","Sue","Richard","Juan","Peter","Micheal","Olga","Sam","Olaf","Sasha","Eliza","Alan"]
                for n in range(settings.populationSize):
                    newNet = NeuralNet(name = names[n%len(names)])
                    for each in range(50):
                            newNet.mutate()
                    newNet.train()
                    self.population.addIfBetter(newNet)
                    del newNet
                newStage = 1
            elif settings.stage == 1:
                self.childNN = self.population.getAChild(settings.maxMutations)
                neuralNetBreederApp.mainWindow.rightNet.setToNN(self.childNN)
                newStage = 2
            elif settings.stage == 2:
                self.population.addIfBetter(self.childNN)
                self.population.setBestUI()
                newStage = 1
            settings.stage = newStage

class NeuralNet():
    def __init__(self,
                 name               = "Eve",
                 generation         = 1,
                 connection_rate    = 0.5,
                 learning_rate      = 0.5,
                 max_iterations     = 50,
                 bornBefore         = 0,
                 trainAlg           = libfann.FANN_TRAIN_RPROP,
                 learning_momentum  = 0.0,
                 neurons            = [],
                 connectionType     = "Sparse"):
        settings.netsTried     += 1
        self.name               = name
        self.generation         = generation
        self.connection_rate    = connection_rate
        self.learning_rate      = learning_rate
        self.max_iterations     = max_iterations
        self.ann                = ""
        self.childrenHad        = 0
        self.bornBefore         = bornBefore
        self.trainAlg           = trainAlg
        self.learning_momentum  = learning_momentum
        self.mseHistory         = []
        self.testmseHistory     = []
        self.summedError        = 1.0
        self.neurons            = copy.deepcopy(neurons)
        if (self.neurons == []):
            self.neurons = [[[settings.flist[random.randrange(len(settings.flist))],0.0001+(0.9999*random.random())],
                             [settings.flist[random.randrange(len(settings.flist))],0.0001+(0.9999*random.random())]] , 
                            [[settings.flist[random.randrange(len(settings.flist))],0.0001+(0.9999*random.random())] 
                               for i in range(settings.num_output)]]
        self.foodcost    = (0.001*(len(self.neurons)-1)) + (0.0001*sum(map(len,self.neurons[0:-1])))
        self.connectionType = connectionType
        if self.ann =="":
            self.ann = libfann.neural_net()
    def getChild(self, num_mutations):
        self.childrenHad = self.childrenHad + 1
        newANN = NeuralNet(name               = (self.getNameStub(self.name) + "-" + str(self.generation + 1) + "-" +
                                                 str(self.childrenHad) + "-" + str(self.bornBefore + self.childrenHad)),
                           generation         = self.generation + 1,
                           connection_rate    = self.connection_rate,
                           learning_rate      = self.learning_rate,
                           max_iterations     = self.max_iterations,
                           bornBefore         = self.bornBefore + self.childrenHad,
                           trainAlg           = self.trainAlg,
                           learning_momentum  = self.learning_momentum,
                           neurons            = self.neurons,
                           connectionType     = self.connectionType)
        newANN.ann.set_quickprop_decay(self.ann.get_quickprop_decay())
        newANN.ann.set_quickprop_mu(self.ann.get_quickprop_mu())
        newANN.ann.set_rprop_increase_factor(self.ann.get_rprop_increase_factor())
        newANN.ann.set_rprop_decrease_factor(self.ann.get_rprop_decrease_factor())
        newANN.ann.set_rprop_delta_min(self.ann.get_rprop_delta_min())
        newANN.ann.set_rprop_delta_max(self.ann.get_rprop_delta_max())
#        newANN.ann.set_rprop_delta_zero(self.ann.get_rprop_delta_zero())
        for each in range(random.randrange(num_mutations)):
                newANN.mutate()
        newANN.train()
        return newANN
    def mutate(self):
        mutation = settings.mutationlist[random.randrange(len(settings.mutationlist))]
        if mutation == "change_connection_rate":
                self.connection_rate = self.connection_rate + (-0.1+(0.2*random.random()))
                if self.connection_rate<0.001:
                    self.connection_rate = 0.001
                elif self.connection_rate>1.0:
                    self.connection_rate = 1.0
        elif mutation == "change_learning_rate":
                self.learning_rate = self.learning_rate + (-0.1+(0.2*random.random()))
                if self.learning_rate<0.00001:
                    self.learning_rate = 0.00001
                elif self.learning_rate>0.99:
                    self.learning_rate = 0.99
        elif mutation == "change_num_neurons_hidden":
                layerIndex = random.randrange(len(self.neurons)-1)
                if len(self.neurons[layerIndex]) <= 1:
                        self.neurons[layerIndex] = ([[settings.flist[random.randrange(len(settings.flist))],0.0001+(0.9999*random.random())]] + 
                                                    self.neurons[layerIndex])
                elif len(self.neurons[layerIndex]) >= 50:
                        del self.neurons[layerIndex][random.randrange(len(self.neurons[layerIndex]))]
                else:
                        if random.random()>0.5:
                                self.neurons[layerIndex] =  ([[settings.flist[random.randrange(len(settings.flist))],0.0001+(0.9999*random.random())]] + 
                                                             self.neurons[layerIndex])
                        else:
                                del self.neurons[layerIndex][random.randrange(len(self.neurons[layerIndex]))]
        elif mutation == "change_num_layers_hidden":
                if len(self.neurons)==2:
                        self.neurons = [[[settings.flist[random.randrange(len(settings.flist))],0.0001+(0.9999*random.random())]
                                                                for each in range(1+random.randrange(10))]] + self.neurons
                elif len(self.neurons)>=11:
                        del self.neurons[random.randrange(len(self.neurons)-1)]
                elif random.random()>0.5:
                        del self.neurons[random.randrange(len(self.neurons)-1)]
                else:
                        newLayerIndex = random.randrange(len(self.neurons)-1)
                        self.neurons =  (self.neurons[:newLayerIndex] + 
                                         [[[settings.flist[random.randrange(len(settings.flist))],0.0001+(0.9999*random.random())] 
                                          for each in range(1+random.randrange(10))]] + self.neurons[newLayerIndex:])
        elif mutation == "change_max_iterations":
                self.max_iterations = int(float(self.max_iterations) * (0.5+(random.random())))
                if self.max_iterations<10:
                    self.max_iterations = 10
                elif self.max_iterations>50000:
                    self.max_iterations = 50000
        elif mutation ==  "change_training_algorithm":
            p = random.random()
            if p < 0.25:
                self.trainAlg = libfann.FANN_TRAIN_BATCH
            elif p < 0.5:
                self.trainAlg = libfann.FANN_TRAIN_RPROP
            elif p < 0.75:
                self.trainAlg = libfann.FANN_TRAIN_INCREMENTAL
            else:
                self.trainAlg = libfann.FANN_TRAIN_QUICKPROP
        elif mutation ==  "change_activation_function_hidden":
                layerIndex = random.randrange(len(self.neurons)-1)
                neuronIndex = random.randrange(len(self.neurons[layerIndex]))
                self.neurons[layerIndex][neuronIndex][0] = settings.flist[random.randrange(len(settings.flist))]
        elif mutation ==  "change_activation_function_output":
                layerIndex = -1
                neuronIndex = random.randrange(len(self.neurons[layerIndex]))
                self.neurons[layerIndex][neuronIndex][0] = settings.flist[random.randrange(len(settings.flist))]
        elif mutation ==  "change_learning_momentum":
                self.learning_momentum = self.learning_momentum + (-0.1+(0.2*random.random()))
                if self.learning_momentum<0.0:
                    self.learning_momentum = 0.0
                elif self.learning_momentum>0.99:
                    self.learning_momentum = 0.99
        elif mutation ==  "change_activation_steepness_hidden":
                layerIndex = random.randrange(len(self.neurons)-1)
                neuronIndex = random.randrange(len(self.neurons[layerIndex]))
                new = self.neurons[layerIndex][neuronIndex][1] + (-0.1+(0.2*random.random()))
                if new <0.0001:
                    new = 0.001
                elif new > 0.9999:
                    new = 0.9999
                self.neurons[layerIndex][neuronIndex][1] = new
        elif mutation ==  "change_activation_steepness_output":
                layerIndex = -1
                neuronIndex = random.randrange(len(self.neurons[layerIndex]))
                new = self.neurons[layerIndex][neuronIndex][1] + (-0.1+(0.2*random.random()))
                if new <0.0001:
                    new = 0.001
                elif new > 0.9999:
                    new = 0.9999
                self.neurons[layerIndex][neuronIndex][1] = new
        elif mutation ==  "change_training_param":
                trmutation = settings.trmutlist[random.randrange(len(settings.trmutlist))]
                if trmutation == "change_connection_type":
                    if self.connectionType == 'Sparse':
                        self.connectionType = 'Shortcut'
                    elif self.connectionType == 'Shortcut':
                        self.connectionType = 'Sparse'
                elif trmutation == "change_quickprop_decay":
                    new = self.ann.get_quickprop_decay()
                    new = new * (2.0*random.random())
                    if new < -0.3:
                        new = -0.3
                    elif new >= 0.0 :
                        new = -0.0000001
                    self.ann.set_quickprop_decay(new)
                elif trmutation == "change_quickprop_mu":
                    new = self.ann.get_quickprop_mu()
                    new = new * (0.6+(0.8*random.random()))
                    if new <= 1.0:
                        new = 1.000001
                    elif new >= 3.0 :
                        new = 3.0
                    self.ann.set_quickprop_mu(new)
                elif trmutation == "change_rprop_increase_factor":
                    new = self.ann.get_rprop_increase_factor()
                    new = new * (0.6+(0.8*random.random()))
                    if new <= 1.0:
                        new = 1.000001
                    elif new >= 3.0 :
                        new = 3.0
                    self.ann.set_rprop_increase_factor(new)
                elif trmutation == "change_rprop_decrease_factor":
                    new = self.ann.get_rprop_decrease_factor()
                    new = new * (0.6+(0.8*random.random()))
                    if new <= 0.0:
                        new = 0.000001
                    elif new >= 1.0 :
                        new = 0.99999
                    self.ann.set_rprop_decrease_factor(new)
                elif trmutation == "change_rprop_delta_min":
                    new = self.ann.get_rprop_delta_min()
                    new = new * (0.6+(0.8*random.random()))
                    if new <= 0.0:
                        new = 0.0
                    elif new >= 1.0 :
                        new = 0.99999
                    self.ann.set_rprop_delta_min(new)
                elif trmutation == "change_rprop_delta_max":
                    new = self.ann.get_rprop_delta_max()
                    new = new * (0.6+(0.8*random.random()))
                    if new <= 1.0:
                        new = 1.0
                    elif new >= 200.0 :
                        new = 200.0
                    self.ann.set_rprop_delta_max(new)
#                elif trmutation == "change_rprop_delta_zero":
#                    new = self.ann.get_rprop_delta_zero()
#                    new = new * (0.6+(0.8*random.random()))
#                    if new <= 0.0:
#                        new = 0.0001
#                    elif new >= 20.0 :
#                        new = 20.0
#                    self.ann.set_rprop_delta_zero(new)
        self.foodcost    = (0.001*(len(self.neurons)-1)) + (0.0001*sum(map(len,self.neurons[0:-1])))
    def train(self):
        self.ann.set_learning_momentum(self.learning_momentum)
        self.ann.set_training_algorithm(self.trainAlg)
        if self.connectionType == 'Sparse':
            self.ann.create_sparse_array(self.connection_rate, [settings.num_input]+map(len,self.neurons))
        elif self.connectionType == 'Shortcut':
            self.ann.create_shortcut_array([settings.num_input]+map(len,self.neurons))
        self.ann.set_learning_rate(self.learning_rate)
        for layerIndex in range(len(self.neurons)):
            for neuronIndex in range(len(self.neurons[layerIndex])):
                funcSteep = self.neurons[layerIndex][neuronIndex]
                self.ann.set_activation_function(funcSteep[0],layerIndex+1,neuronIndex)
                self.ann.set_activation_steepness(funcSteep[1],layerIndex+1,neuronIndex)
        itsLeft = self.max_iterations
        while itsLeft > 0:
            self.ann.train_on_data(settings.trainingData, 1, settings.iterations_between_reports, settings.desired_error)
            itsLeft = itsLeft - 1
            self.mseHistory.append(self.ann.get_MSE())
            t = self.ann.test_data(settings.testData)
            self.testmseHistory.append(t)
        self.foodcost    = 0.0000001*float(self.ann.get_total_connections())
        self.summedError = 0.9*self.mseHistory[-1] + 1.1*self.testmseHistory[-1] + self.foodcost
        if str(self.summedError) == 'nan':
            self.summedError = 9999999.0
        neuralNetBreederApp.mainWindow.updateNumberOfNets()
    def getNameStub(self,name):
        result = name
        if '-' in result:
                result = result[0:name.index('-')]
        return result

class NeuralNetPopulation():
    def __init__(self,maxSize = 5):
        self.maxSize  = maxSize
        self.subjects = []
        self.lastSavedName = ""
    def addIfBetter(self,newSubject):
        if len(self.subjects)< self.maxSize:
                self.subjects.append(newSubject)
                subjectIndex = len(self.subjects)-1
                neuralNetBreederApp.mainWindow.subjectPanels[subjectIndex].setToNN(self.subjects[subjectIndex])
        else:
                newTotalValue = newSubject.summedError                
                highestTotalIndex = 0
                highestTotalValue = 0.0
                for subjectIndex in range(len(self.subjects)):
                        if highestTotalValue < self.subjects[subjectIndex].summedError:
                                highestTotalValue = self.subjects[subjectIndex].summedError
                                highestTotalIndex = subjectIndex
                if newTotalValue< highestTotalValue:
                        self.subjects[highestTotalIndex] = newSubject
                        neuralNetBreederApp.mainWindow.subjectPanels[highestTotalIndex].setToNN(self.subjects[highestTotalIndex])
    def getAChild(self,maxMutations):
        return (self.subjects[random.randrange(len(self.subjects))].getChild(maxMutations))
    def setBestUI(self):
        bestIndex = 0
        bestTotalValue = 100.0
        worstTotalValue = 0.0
        for subjectIndex in range(len(self.subjects)):
                if self.subjects[subjectIndex].summedError < bestTotalValue:
                        bestIndex = subjectIndex
                        bestTotalValue = self.subjects[subjectIndex].summedError
                if self.subjects[subjectIndex].summedError > worstTotalValue:
                        worstTotalValue = self.subjects[subjectIndex].summedError
        neuralNetBreederApp.mainWindow.leftNet.setToNN(self.subjects[bestIndex])
        if self.subjects[bestIndex].name != self.lastSavedName:
                self.lastSavedName = self.subjects[bestIndex].name
                self.subjects[bestIndex].ann.save(settings.datafile+".net")
        if worstTotalValue*0.5 >= 0.25:
            fr = 255
            fg = 0
            fb = 0
        elif worstTotalValue*0.5 >= 0.125:
            fr = 255
            fg = int((1.0-((worstTotalValue*0.5-0.125)*8.0))*255.0)
            fb = 0
        else:
            fr = int(((worstTotalValue*0.5)*8.0)*255.0)
            fg = 255
            fb = 0
        if bestTotalValue*0.5 >= 0.25:
            tr = 255
            tg = 0
            tb = 0
        elif bestTotalValue*0.5 >= 0.125:
            tr = 255
            tg = int((1.0-((bestTotalValue*0.5-0.125)*8.0))*255.0)
            tb = 0
        else:
            tr = int(((bestTotalValue*0.5)*8.0)*255.0)
            tg = 255
            tb = 0
        neuralNetBreederApp.setIcon(fr,fg,fb,tr,tg,tb)

class ErrorCanvas(WXElements.GLCanvasBase):
   def InitGL(self):
       self.history = []
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
       if len(self.history)>=2:
            wave_array = []
            for historyIndex in range(len(self.history)):
                    wave_array.append([-1.0 + (2.0 * (float(historyIndex)/float(len(self.history)-1)) ),
                                       -1.0 + (8.0 *self.history[historyIndex])])
                    wave_array.append([-1.0 + (2.0 * (float(historyIndex)/float(len(self.history)-1)) ),
                                       -1.0 ])
            if self.history[-1] >= 0.25:
                glColor(1.0,0.0,0.0)  
            elif self.history[-1] >= 0.125:
                glColor(1.0,1.0-((self.history[-1]-0.125)*8.0),0.0)
            else:
                glColor(((self.history[-1])*8.0),1.0,0.0)
            glVertexPointerf(wave_array)
            glDrawArrays(GL_QUAD_STRIP, 0, len(wave_array))
       self.SwapBuffers()
   def setHistory(self, history):
        self.history = history
        self.Refresh()
        self.Update()
      
class NetPanel(wx.Panel):
    def __init__(self, parent,panellabel):        
        wx.Panel.__init__(self, parent)
        panelSizer = wx.FlexGridSizer(0,1,0,0)
        panelSizer.AddGrowableCol(0)
        panelText = wx.StaticText(self,label=panellabel)
        panelSizer.Add(panelText, 0, wx.ALIGN_LEFT|wx.ALL, 4)
        nb = wx.Notebook(self)
        page1 = wx.Panel(nb)
        page1Sizer = wx.FlexGridSizer(0,1,0,0)
        page1Sizer.AddGrowableCol(0)
        self.nameText = wx.StaticText(page1,label=" ")
        page1Sizer.Add(self.nameText, 0, wx.ALIGN_LEFT|wx.ALL, 4)
        self.layerSummaryText = wx.StaticText(page1,label="\n")
        page1Sizer.Add(self.layerSummaryText, 0, wx.ALIGN_LEFT|wx.ALL, 4)
        self.connection_rateText = wx.StaticText(page1,label="")
        page1Sizer.Add(self.connection_rateText, 0, wx.ALIGN_LEFT|wx.ALL, 4)
        page1.SetSizer(page1Sizer)
        nb.AddPage(page1,"Neural net")
        page2 = wx.Panel(nb)
        page2Sizer = wx.FlexGridSizer(0,1,0,0)
        page2Sizer.AddGrowableCol(0)
        self.trainAlgText = wx.StaticText(page2,label="")
        page2Sizer.Add(self.trainAlgText, 0, wx.ALIGN_LEFT|wx.ALL, 4)
        self.learning_rateText = wx.StaticText(page2,label="")
        page2Sizer.Add(self.learning_rateText, 0, wx.ALIGN_LEFT|wx.ALL, 4)
        self.learning_momentumText = wx.StaticText(page2,label="")
        page2Sizer.Add(self.learning_momentumText, 0, wx.ALIGN_LEFT|wx.ALL, 4)
        self.max_iterationsText = wx.StaticText(page2,label="")
        page2Sizer.Add(self.max_iterationsText, 0, wx.ALIGN_LEFT|wx.ALL, 4)
        page2.SetSizer(page2Sizer)
        nb.AddPage(page2,"Training")
        page3 = wx.Panel(nb)
        page3Sizer = wx.FlexGridSizer(0,1,0,0)
        page3Sizer.AddGrowableCol(0)
        page3Sizer.AddGrowableRow(0)
        self.nn = ""
        printButton = wx.Button(page3, label="Print to console")
        printButton.Bind(wx.EVT_BUTTON, self.printDetails)
        page3Sizer.Add(printButton, 0, wx.ALIGN_CENTER|wx.ALL, 4)
        page3.SetSizer(page3Sizer)
        nb.AddPage(page3,"Details")
        panelSizer.Add(nb, 0, wx.EXPAND|wx.ALL, 4)
        self.errorText = wx.StaticText(self,label="")
        panelSizer.Add(self.errorText, 0, wx.ALIGN_LEFT|wx.ALL, )
        self.errorCanvas = ''
        if noGL:
            self.errorCanvas = WXElements.NoGLVisualizationPanel(self)
        else:
            self.errorCanvas = ErrorCanvas(self)
        panelSizer.AddGrowableRow(3)
        panelSizer.Add(self.errorCanvas, 0, wx.EXPAND|wx.ALL, 4)
        self.testerrorCanvas = ''
        if noGL:
            self.testerrorCanvas = WXElements.NoGLVisualizationPanel(self)
        else:
            self.testerrorCanvas = ErrorCanvas(self)
        self.testerrorText = wx.StaticText(self,label="")
        panelSizer.Add(self.testerrorText, 0, wx.ALIGN_LEFT|wx.ALL, 4)
        panelSizer.AddGrowableRow(5)
        panelSizer.Add(self.testerrorCanvas, 0, wx.EXPAND|wx.ALL, 4)
        self.foodText = wx.StaticText(self,label="")
        panelSizer.Add(self.foodText, 0, wx.ALIGN_LEFT|wx.ALL, 4)
        self.qlText = wx.StaticText(self,label="")
        panelSizer.Add(self.qlText, 0, wx.ALIGN_LEFT|wx.ALL, 4)
        self.SetSizer(panelSizer)
        self.SetAutoLayout(1)
    def setToNN(self,neuralnet):
        self.nn = neuralnet
        self.nameText.SetLabel(" Name: "+neuralnet.name)
        self.max_iterationsText.SetLabel(" Training Epochs: "+str(neuralnet.max_iterations))
        self.learning_rateText.SetLabel(" Learning rate: "+str(neuralnet.learning_rate))
        if (neuralnet.connectionType=='Sparse'):
            self.connection_rateText.SetLabel(" "+str(neuralnet.ann.get_total_connections())+" Connections (no shortcuts)")
        elif  (neuralnet.connectionType=='Shortcut'):
            self.connection_rateText.SetLabel(" "+str(neuralnet.ann.get_total_connections())+" Connections (including shortcuts)")
        self.foodText.SetLabel(" Energy required: "+str(neuralnet.foodcost))
        self.layerSummaryText.SetLabel(" "+str(1+len(neuralnet.neurons))+" Layers ("+
                                           str(len(neuralnet.neurons)-1)+" hidden)\n "+
                                           str(settings.num_input  + sum(map(len,neuralnet.neurons)))+" Nodes total ("+
                                           str(settings.num_input)+" in, "+
                                           str(sum(map(len,neuralnet.neurons[0:-1])))+" hidden, "+
                                           str(len(neuralnet.neurons[-1]))+" out)")
        self.layerSummaryText.SetToolTip(wx.ToolTip("Nodes per layer: "+str([settings.num_input]+map(len,neuralnet.neurons))))
        if neuralnet.trainAlg == 0:
            self.trainAlgText.SetLabel(" Training algorithm: Backprop incremental")
            self.trainAlgText.SetToolTip(wx.ToolTip("no special settings"))
        elif neuralnet.trainAlg == 1:
            self.trainAlgText.SetLabel(" Training algorithm: Backprop batch")
            self.trainAlgText.SetToolTip(wx.ToolTip("no special settings"))
        elif neuralnet.trainAlg == 2:
            self.trainAlgText.SetLabel(" Training algorithm: iRPROP batch")
            self.trainAlgText.SetToolTip(wx.ToolTip("increase factor: "+str(neuralnet.ann.get_rprop_increase_factor())+"\n"+
                                         "decrease factor: "+str(neuralnet.ann.get_rprop_decrease_factor())+"\n"+
                                         "delta min: "+str(neuralnet.ann.get_rprop_delta_min())+"\n"+
                                         "delta max: "+str(neuralnet.ann.get_rprop_delta_max())))
        elif neuralnet.trainAlg == 3:
            self.trainAlgText.SetLabel(" Training algorithm: quickprop batch")
            self.trainAlgText.SetToolTip(wx.ToolTip("decay: "+str(neuralnet.ann.get_quickprop_decay())+"\n"+
                                         "mu: "+str(neuralnet.ann.get_quickprop_mu())))
        self.learning_momentumText.SetLabel(" Learning momentum: "+str(neuralnet.learning_momentum))
        self.errorText.SetLabel(" Mean Square Error: "+str(neuralnet.mseHistory[-1]))
        self.testerrorText.SetLabel(" Test MSE: "+str(neuralnet.testmseHistory[-1]))
        self.errorCanvas.setHistory(neuralnet.mseHistory)
        self.testerrorCanvas.setHistory(neuralnet.testmseHistory)
        self.qlText.SetLabel(" Total Quality: "+str(1.0-(2.0*neuralnet.summedError)))
    def printDetails(self, event=None):
        if self.nn != "":
            print ("\nDetails about "+self.nameText.GetLabel()[7:]+":\n")
            self.nn.ann.print_parameters()
            self.nn.ann.print_connections()
        else:
            print ("\nYou have not started breeding yet.\n")

class GUIMain(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,None,title="Triathlon Breeder",size=(300,600))
        self.panel = wx.Panel(self, wx.ID_ANY)
        MenuBar = wx.MenuBar()
        self.FileMenu = wx.Menu()
        item = self.FileMenu.Append(wx.ID_EXIT, text="Quit")
        self.Bind(wx.EVT_MENU, self.OnQuit, item)
        MenuBar.Append(self.FileMenu, "Menu")
        self.SetMenuBar(MenuBar)
        sizer = wx.FlexGridSizer(0,1,0,0)
        sizer.AddGrowableCol(0)
        self.netsTried = wx.StaticText(self.panel,label="Neural nets tried: 0")
        sizer.Add(self.netsTried, 0, wx.EXPAND|wx.ALL, 2)
        self.playButton = wx.Button(self.panel, label="Start breeding")
        self.playButton.Bind(wx.EVT_BUTTON, self.OnPlay)
        sizer.Add(self.playButton, 0, wx.EXPAND|wx.ALL, 2)
        categoryNotebook = wx.Notebook(self.panel)
        self.leftNet = NetPanel(categoryNotebook,"\n Best Translator\n (saved as "+settings.datafile+".net)\n")
        self.rightNet = NetPanel(categoryNotebook,"\n New Translator\n (to be tested)\n")
        subjectNBPanel = wx.Panel(categoryNotebook)
        subjectNBSizer = wx.FlexGridSizer(0,1,0,0)
        subjectNB = wx.Notebook(subjectNBPanel)
        subjectNBSizer.AddGrowableCol(0)
        subjectNBSizer.Add(wx.StaticText(subjectNBPanel,label=""), 0, wx.EXPAND|wx.ALL , 0)
        subjectNBSizer.AddGrowableRow(1)
        subjectNBSizer.Add(subjectNB, 0, wx.EXPAND)
        subjectNBPanel.SetSizer(subjectNBSizer)
        self.subjectPanels = []
        for i in range(settings.populationSize):
                self.subjectPanels.append(NetPanel(subjectNB," Population member"))
                subjectNB.AddPage(self.subjectPanels[i],str(i+1))
        categoryNotebook.AddPage(self.leftNet,"Best")
        categoryNotebook.AddPage(subjectNBPanel,"Population")
        categoryNotebook.AddPage(self.rightNet,"New")
        sizer.AddGrowableRow(2)
        sizer.Add(categoryNotebook, 0, wx.EXPAND|wx.ALL , 2)
        self.panel.SetSizer(sizer)
        self.panel.Layout()
    def OnQuit(self, event=None):
        self.Close()
    def OnPlay(self, event=None):
        if settings.breeding:
                settings.breeding = False
                self.playButton.SetLabel("Continue breeding")
        else:
                settings.breeding = True
                self.playButton.SetLabel("Pause breeding")
    def updateNumberOfNets(self):
        self.netsTried.SetLabel("Neural nets tried: "+str(settings.netsTried))

class NeuralNetBreederApp(wx.App):
    def __init__(self, redirect = False):
        wx.App.__init__(self)
        ib = wx.IconBundle()
        bmp = self.make_grad_image(32,32, (0,0,0), (0,0,0))
        icon = wx.EmptyIcon()
        icon.CopyFromBitmap(bmp)
        ib.AddIcon(icon)
        self.mainWindow = GUIMain()
        self.setIcon(0,0,0,0,0,0)
        self.mainWindow.Show(True)
    def setIcon(self,from_r,from_g,from_b,to_r,to_g,to_b):
        ib = wx.IconBundle()
        bmp = self.make_grad_image(32,32, (from_r,from_g,from_b), (to_r,to_g,to_b))
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
    datafile = ""
    if len(sys.argv)<2:
        path = os.getcwd()
        fileList = os.listdir(path)
        profileList = []
        for fileName in fileList:
            if fileName[-5:] == "train":
                profileList.append(fileName[:-6])
        if len(profileList) > 0:
            datafile = str(WXElements.selection("Select your Sample-set",profileList[0], profileList))
        else:
            print "Error: no profiles found"
    else:
        datafile = sys.argv[1]
    if len(datafile)==0:
        print ( "If you want to breed a neural net based on myProfile.train and myProfile.test,\n"+
                "use: python Triathlon-Breeder.py myProfile")
    else:
        if os.path.exists(datafile+".train") and os.path.exists(datafile+".test"):
            settings = AppSettings(datafile)
            neuralNetBreederApp = NeuralNetBreederApp()
            breedTimer = BreedingEventTimer()
            neuralNetBreederApp.MainLoop()
        else:
            print "Error: no "+datafile+".train file\nor no "+datafile+".test file found."  
