# -*- coding: iso-8859-1 -*-
import numpy
import usb
import sys

OCZ_NIA = 0
OCZ_NIAx2 = 1

SupportedDevices = {}
SupportedDevices["OCZ Neural Impulse Actuator"] = OCZ_NIA
SupportedDevices["2x OCZ Neural Impulse Actuator"] = OCZ_NIAx2

class NIA_Interface():
    def __init__(self, skipNIAs):
        self.VENDOR_ID = 0x1234 #: Vendor Id
        self.PRODUCT_ID = 0x0000 #: Product Id for the bridged usb cable
        self.TIME_OUT = 100
        self.handle = None
        self.device = None
        buses = usb.busses()
        found = False
        for bus in buses :
            for device in bus.devices :
                if device.idVendor == self.VENDOR_ID and device.idProduct == self.PRODUCT_ID:
                    if skipNIAs == 0:
                        self.device = device
                        self.config = self.device.configurations[0]
                        self.interface = self.config.interfaces[0][0]
                        self.ENDPOINT1 = self.interface.endpoints[0].address
                        self.ENDPOINT2 = self.interface.endpoints[1].address
                        self.PACKET_LENGTH = self.interface.endpoints[0].maxPacketSize
                        found = True
                        break
                    else:
                        skipNIAs -= 1
            if found:
                break
                
    def open(self) :
        if not self.device:
            from sys import stderr
            stderr.write("Error: could not find enough nia-devices")
            sys.exit(0)
        try:
            self.handle = self.device.open()
            self.handle.detachKernelDriver(0)
            self.handle.detachKernelDriver(1)
            self.handle.setConfiguration(self.config)
            self.handle.claimInterface(self.interface)
            self.handle.setAltInterface(self.interface)
        except usb.USBError, err:
            #if False:            # usb debug info
            from sys import stderr
            stderr.write(err)
            
    def close(self):
        try:
            self.handle.reset()
            self.handle.releaseInterface()
        except Exception, err:
           from sys import stderr
           stderr.write(err)
           
        self.handle, self.device = None, None
        
    def read(self):
        try:
            return self.handle.interruptRead(self.ENDPOINT1,self.PACKET_LENGTH,self.TIME_OUT)
        except usb.USBError, err:
            print "Pulled out the NIA device, accidentally?"
            from sys import stderr
            stderr.write(err)
            self.close()
            sys.exit(-1)

class NIA_Data():
    def __init__(self,point,skipNIAs) :
        self.Points = point # there is a point every ~2 ms
        self.Working_Data = []
        self.Hamming = numpy.hamming(256)
        self.interface = NIA_Interface(skipNIAs)
        self.interface.open()
        self.calibrate()
        
    def calibrate(self):
        while len(self.Working_Data)<3844:
            self.record()
        self.Calibration = sum(self.Working_Data)/len(self.Working_Data)
        self.process()
        
    def record(self):
        current_data = [] # prepares a new list to store the read NIA data
        for a in range(self.Points):
            raw_data = self.interface.read()
            for b in xrange(int(raw_data[54])): # byte 54 gives the number of samples
                current_data.append(raw_data[b*3+2]*65536 + raw_data[b*3+1]*256 + raw_data[b*3] - 800000)
        self.Working_Data = (self.Working_Data+current_data)[-3845:-1] # GIL prevents bugs here.
        
    def process(self):
        filtered = numpy.fft.fft(
                map(lambda v,w,x,y,z: (v+2*w+3*x+2*y+z)/(9.0*self.Calibration), 
                        self.Working_Data[0:-4],
                        self.Working_Data[1:-3], 
                        self.Working_Data[2:-2], 
                        self.Working_Data[3:-1], 
                        self.Working_Data[4:])[::15]*self.Hamming)
        self.Frequencies = list(abs(filtered))

class BCIDevice():
    def __init__(self,deviceString):
        self.devices = []
        self.deviceType = SupportedDevices[deviceString]
        if self.deviceType == OCZ_NIA:
            self.devices.append(NIA_Data(25,0))
        elif self.deviceType == OCZ_NIAx2:
            self.devices.append(NIA_Data(25,0))
            self.devices.append(NIA_Data(25,1))
            
    def frequencies(self,i,fromFreq,toFreq):
        return self.devices[i].Frequencies[fromFreq:toFreq]
        
    def frequenciesCombined(self,fromFreq,toFreq):
        result = []
        for i in range(len(self.devices)):
            result.extend(self.frequencies(i,fromFreq,toFreq))
        return result
        
    def process(self,i):
        self.devices[i].process()
        
    def record(self,i):
        self.devices[i].record()
        
    def calibrate(self,i):
        self.devices[i].calibrate()
        
    def calibrateAll(self):
        for i in range(len(self.devices)):
            self.calibrate(i)
            
    def working_Data(self,i):
        return self.devices[i].Working_Data
        
    def calibration(self,i):
        return self.devices[i].Calibration
        
    def setPoints(self,po):
        for i in range(len(self.devices)):
            self.devices[i].Points = po

if __name__ == "__main__":
    import WXElements
    selection = WXElements.selection("Select your Device",SupportedDevices.keys()[0],SupportedDevices.keys())
    bciDevice = BCIDevice(selection)
    print bciDevice.frequenciesCombined(10,30)
