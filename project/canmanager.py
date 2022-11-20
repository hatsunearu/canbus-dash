import can
import abc
import time

class CanBusManager():
    def __init__(self, channel, posthook, interface='socketcan', decoders=[]):
        self._bus = can.interface.Bus(channel=channel, interface=interface)
        self.decoders = {d.id : d for d in decoders}
        self._bus.set_filters([self.filter_from_decoder(d) for d in decoders])
        self.posthook = posthook
        self.can_last_live = 0

        custom_listener = CanBusManagerListener(self)

        self.notifier = can.Notifier(self._bus, listeners=[custom_listener])
        
    

    @staticmethod
    def filter_from_decoder(decoder, extended=False):
        if extended:
            mask = 0x1fffffff # 29 bits
        else:
            mask = 0x7ff # 11 bits
        return {"can_id": decoder.id, "can_mask": mask, "extended": extended}
    

class CanBusManagerListener(can.Listener):
    def __init__(self, manager: CanBusManager):
        self.manager = manager
    
    def on_message_received(self, mesg: can.Message):
        decoder = self.manager.decoders[mesg.arbitration_id]
        data = decoder.decode(mesg.data)
        self.manager.posthook(data=data, timestamp=mesg.timestamp)
    
