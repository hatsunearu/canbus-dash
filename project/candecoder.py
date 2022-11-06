from collections import namedtuple
import abc, can
import canmanager

class CanMessageDecoder(abc.ABC):
    @property
    @classmethod
    @abc.abstractmethod
    def id():
        pass

    def __init__(self, id):
        pass

    @classmethod
    @abc.abstractmethod
    def decode(self, can_message: can.Message):
        pass

class Can201Decoder(CanMessageDecoder):

    result = namedtuple('Can201Result', ['rpm', 'speed', 'accpos', 'can201unknown1'])

    id = 0x201

    @classmethod
    def decode(cls, data):
        rpm = (data[0] * 255 + data[1])/4.
        speed = (data[4] * 255 + data[5])/100. - 100.
        accpos = data[6]/2.0
        can201unknown1 = (data[2] * 255 + data[3]) - 0x7fff
        return cls.result(rpm, speed, accpos, can201unknown1)

class Can240Decoder(CanMessageDecoder):

    result = namedtuple('Can240Result', 
        ['calcload', 'ect', 'can240unknown1', 'throttlevalve', 'iat'])
    
    id = 0x240

    @staticmethod
    def decode(cls, data):
        calcload = 100*data[0]/255.00
        ect = data[1]-40
        can240unknown1 = data[2]
        throttlevalve = 100*data[3]/255.00
        iat = data[4]-40
        return cls.result(calcload, ect, can240unknown1, throttlevalve, iat)

class Can231Decoder(CanMessageDecoder):
    
    result = namedtuple('Can231Result', 
        ['clutch', 'gearneutral'])
    
    id = 0x231

    @classmethod
    def decode(cls, data):
        gearneutral = bool(0x04 & data[1])
        clutch = bool(0x02 & data[1])
        return cls.result(clutch, gearneutral)