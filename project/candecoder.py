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


def unimplemented_CanDecoder_factory(canid) -> CanMessageDecoder:
    
    class UnimplementedCanDecoder(CanMessageDecoder):
        
        result = namedtuple(f'Can{canid:X}Result', [f'can{canid:X}total'])
        
        id = canid

        @classmethod
        def decode(cls, data):
            return cls.result(data)

    return UnimplementedCanDecoder



class Can200Decoder(CanMessageDecoder):

    result = namedtuple('Can200Result', ['brake', 'can200total'])

    id = 0x200

    @classmethod
    def decode(cls, data):
        brake = bool(data[6] & 0x1)
        return cls.result(brake, data)

class Can201Decoder(CanMessageDecoder):

    result = namedtuple('Can201Result', ['rpm', 'speed', 'accpos', 'can201unknown1', 'can201total'])

    id = 0x201

    @classmethod
    def decode(cls, data):
        rpm = (data[0] * 255 + data[1])/4.
        speed = (data[4] * 255 + data[5])/100. - 100.
        accpos = data[6]/2.0
        can201unknown1 = (data[2] * 255 + data[3]) - 0x7fff
        return cls.result(rpm, speed, accpos, can201unknown1, data)

Can211Decoder = unimplemented_CanDecoder_factory(0x211)
Can212Decoder = unimplemented_CanDecoder_factory(0x212)
Can215Decoder = unimplemented_CanDecoder_factory(0x215)

class Can231Decoder(CanMessageDecoder):
    
    result = namedtuple('Can231Result', 
        ['clutch', 'gearneutral', 'can231total'])
    
    id = 0x231

    @classmethod
    def decode(cls, data):
        gearneutral = bool(0x04 & data[1])
        clutch = bool(0x02 & data[1])
        return cls.result(clutch, gearneutral, data)

class Can240Decoder(CanMessageDecoder):

    result = namedtuple('Can240Result', 
        ['calcload', 'ect', 'can240unknown1', 'throttlevalve', 'iat', 'can240total'])
    
    id = 0x240

    @classmethod
    def decode(cls, data):
        calcload = 100*data[0]/255.00
        ect = data[1]-40
        can240unknown1 = data[2]
        throttlevalve = 100*data[3]/255.00
        iat = data[4]-40
        return cls.result(calcload, ect, can240unknown1, throttlevalve, iat, data)

Can420Decoder = unimplemented_CanDecoder_factory(0x420)
Can430Decoder = unimplemented_CanDecoder_factory(0x430)
