from .inputs import Input
import time

buttonCodes = {65527:'Down', 
                65533:'Up', 
                65534:'Right', 
                65531:'Left', 
                65519:'Space'}
                
debug = False

## Class ##
class RESPONSEPixx(Input):
    """
    An implementation of Input for the RESPONSEPixx box. Accepted keys are 'Up',
    'Down', 'Left', 'Right', 'Space', and 'Escape' which correspond to the
    colours of the RESPONSEPixx, or the actual Escape key in the case of
    'Escape'. These names were chosen to be uniform with the Keyboard
    implementation.
    """

    def __init__(self, device):
        super(RESPONSEPixx,self).__init__()
        self.device = device
        
        self.log = self.device.din.setDinLog(12e6, 1000)
        self.device.din.startDinLog()
        self.device.updateRegisterCache()
        
        self.startTime = self.device.getTime()
   
    ## new function in HRL3. waitButton() function implemented in python
    ## in previous version of HRL waitButton() was a function of the 
    ## datapixx.so python wrapper
    ## Adapted from example code in: 
    ## https://www.vpixx.com/manuals/python/html/basicdemo.html#example-8-how-to-read-button-presses-from-a-responsepixx
    def waitButton(self, to):
        if debug:
            print('waiting for button press')
        
        self.startTime = self.device.getTime()
        if debug:
            print(self.startTime)
            
        finished = False
        
        while not finished:
            if (self.device.getTime() - self.startTime) > to:
                finished = True
                
            #read device status
            self.device.updateRegisterCache()
            self.device.din.getDinLogStatus(self.log)
            #print(self.log)
            
            newEvents = self.log["newLogFrames"]

            if newEvents > 0:
                eventList = self.device.din.readDinLog(self.log, newEvents)
                #print(eventList)
                
                # taking only the first event
                #for x in eventList:
                x = eventList[0]
                if x[1] != 65535: # ommiting button releases
                    #get the time of the press, since we started logging
                    t = round(x[0] - self.startTime, 5) # 5 decimal precision
                    if debug:
                        printStr = 'Button pressed! Button code: ' + str(x[1]) + ', Time:' + str(t)
                        print(printStr)
                    finished = True
                    return(x[1], t)
           
            time.sleep(0.05) # waiting 50 ms until next software poll.

        return None
    
    
    def readButton(self,btns=None,to=3600):
        if self.checkEscape():
            return ('Escape', -1)

        rspns = self.waitButton(to)
        
        
        if rspns == None:
            return (None, to)
        else:
            (ky,tm) = rspns
            ky = buttonCodes[ky]
            if (btns == None) or (btns.count(ky) > 0):
                return (ky,tm)
            else:
                to -= tm
                (ky1,tm1) = self.readButton(btns,to)
                return (ky1,tm1 + tm)


