import re
import canmanager, candecoder
import pprint

import time, sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer

from ui import Ui_MainWindow


class DisplayManager():

    # reference gear ratios, rpm / vss, in kph
    ref_gear_ratios = [142.91697013838305, 83.27517447657029, 59.904354392147, 42.876771767428416, 36.34426533259218, 30.183701387531755]


    def __init__(self, can_decoders, qtapplication):
        self._last_unstable_gear_time = 0

        self.can_data = {}

        for decoder in can_decoders:
            for field in decoder.result._fields:
                self.can_data[field] = bytearray(0)

        self.app = qtapplication

    
    def filtered_gear(self):
        # too slow, avoid division by zero
        if self.can_data['speed'] < 1:
            self._last_unstable_gear_time = time.time()
            return 'n'

        # detect stable gear ratio
        stable_ratio = None
        for i, r in enumerate(self.ref_gear_ratios):
            if 0.90 < ((self.can_data['rpm'] / self.can_data['speed']) / r) < 1.10:
                stable_ratio = i + 1
                break
        
        # no stable ratio detected, or clutched
        if not stable_ratio or self.can_data['clutch'] or self.can_data['gearneutral']: 
            self._last_unstable_gear_time = time.time()
            return 'n'

        # stable ratio detected, and time passed since last unstable
        elif time.time() - self._last_unstable_gear_time > 0.1:
            return str(stable_ratio)
        
        # stable ratio detected, but timeout has not passed
        # don't update unstable time
        else:
            return 'n'
    
    def format_hex(self, h):
        s = h.hex()
        return s[0:8] + '\n' + s[8:]
        
    def get_can_update(self, data, timestamp):
        for k, v in data._asdict().items():
            self.can_data[k] = v

    def update_displays(self):
        self.app.ui.mphLabel.setText(f"{abs(self.can_data['speed'] * 0.621371):.0f}")
        self.app.ui.rpmProgressbar.setProperty("value", f"{self.can_data['rpm']:.0f}")
        self.app.ui.gearLabel.setText(self.filtered_gear())

        self.app.ui.canlabel200.setText(self.format_hex(self.can_data['can200total']))
        self.app.ui.canlabel201.setText(self.format_hex(self.can_data['can201total']))
        self.app.ui.canlabel212.setText(self.format_hex(self.can_data['can212total']))
        self.app.ui.canlabel215.setText(self.format_hex(self.can_data['can215total']))
        self.app.ui.canlabel231.setText(self.format_hex(self.can_data['can231total']))
        self.app.ui.canlabel240.setText(self.format_hex(self.can_data['can240total']))
        self.app.ui.canlabel420.setText(self.format_hex(self.can_data['can420total']))
        self.app.ui.canlabel430.setText(self.format_hex(self.can_data['can430total']))
        
        

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

def main():

    can_decoders = [candecoder.Can200Decoder, candecoder.Can201Decoder, candecoder.Can211Decoder, \
        candecoder.Can212Decoder, candecoder.Can215Decoder, candecoder.Can231Decoder, \
        candecoder.Can240Decoder, candecoder.Can420Decoder, candecoder.Can430Decoder]

    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()

    dm = DisplayManager(can_decoders=can_decoders, qtapplication=application)
    mgr = canmanager.CanBusManager('vcan0', posthook=dm.get_can_update, decoders=can_decoders)
    

    timer = QTimer(app)
    timer.setInterval(16)
    timer.setSingleShot(False)
    timer.timeout.connect(dm.update_displays)

    timer.start()



    application.show()
    sys.exit(app.exec_())

    

if __name__ == '__main__':
    main()