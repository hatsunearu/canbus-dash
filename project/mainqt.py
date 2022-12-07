import re
import canmanager, candecoder
import pprint, logging, argparse
from abc import ABC, abstractmethod

import time, sys, os

from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer

from ui import Ui_MainWindow


revlimit2 = 6500

class DisplayManager(DataLoggableABC):

    # reference gear ratios, rpm / vss, in kph
    ref_gear_ratios = [142.91697013838305, 83.27517447657029, 59.904354392147, 42.876771767428416, 36.34426533259218, 30.183701387531755]
    
    keys_to_log = ['rpm', 'speed', 'accpos', 'brake', 'clutch', 'ect', 'iat']


    def __init__(self, can_decoders, qtapplication, logfile=None):
        self._last_unstable_gear_time = 0

        self.can_data = {}

        for decoder in can_decoders:
            for field in decoder.result._fields:
                self.can_data[field] = 0 

        self.app = qtapplication
        
        self.last_can_update = 0
        self.canbus_down = True
        self.gps_down = True

        self.state_label_font = self.app.ui.canStateLabel.font()
        f = self.app.ui.canStateLabel.font()
        f.setStrikeOut(True)
        self.state_label_font_strikeout = f

        self.logfile = logfile
        if self.logfile:
            self.logfile.write(f'time,gear,{",".join(self.keys_to_log)}\n')
            logging.info(f'logging enabled to {self.logfile.name}')


    
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
            return stable_ratio
        
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
        self.last_can_update = time.time()

    def update_displays(self):
        rpm = self.can_data['rpm']
        gear = self.filtered_gear()

        self.app.ui.mphLabel.setText(f"{abs(self.can_data['speed'] * 0.621371):.0f}")
        self.app.ui.rpmProgressbar.setProperty("value", f"{rpm:.0f}")
        self.app.ui.rpmLabel.setText(f"{rpm:.0f}")
        self.app.ui.gearLabel.setText(str(gear).upper())
        self.app.ui.ectLabel.setText(f"{self.can_data['ect']:.0f}")
        self.app.ui.iatLabel.setText(f"{self.can_data['iat']:.0f}")

        self.app.ui.clutchProgressbar.setProperty("value", 100 if self.can_data['clutch'] else 0)
        self.app.ui.brakeProgressbar.setProperty("value", 100 if self.can_data['brake'] else 0)
        self.app.ui.gasProgressbar.setProperty("value", self.can_data['accpos'])

        if time.time() - self.last_can_update > 1:
            self.app.ui.canStateLabel.setStyleSheet('font: 18pt "Targa MS"; color: red;')
            self.app.ui.canStateLabel.setFont(self.state_label_font_strikeout)
            self.canbus_down = True
        elif self.canbus_down:
            self.app.ui.canStateLabel.setStyleSheet('font: 18pt "Targa MS"; color: rgb(246, 245, 244);')
            self.app.ui.canStateLabel.setFont(self.state_label_font)
            self.canbus_down = False
        
        # replace with gps down condition
        if True:
            self.app.ui.gpsStateLabel.setStyleSheet('font: 18pt "Targa MS"; color: red;')
            self.app.ui.gpsStateLabel.setFont(self.state_label_font_strikeout)
            self.gps_down = True
        elif self.gps_down:
            self.app.ui.gpsStateLabel.setStyleSheet('font: 18pt "Targa MS"; color: rgb(246, 245, 244);')
            self.app.ui.gpsStateLabel.setFont(self.state_label_font)
            self.gps_down = False
        
        if rpm > revlimit2:
            self.app.ui.rpmProgressbar.setStyleSheet('''
            QProgressBar {
                background-color: #555;
            }
            QProgressBar::chunk {background: rgb(53, 132, 228);}
            ''')
        if gear != 'n' and gear > 1:
            revlimit1 = revlimit2 * self.ref_gear_ratios[gear - 1] / self.ref_gear_ratios[gear - 2]
        else:
            revlimit1 = 5000
        
        if rpm > revlimit2:
            self.app.ui.rpmProgressbar.setStyleSheet('''
            QProgressBar {
                background-color: #555;
            }
            QProgressBar::chunk {background: rgb(224, 27, 36);}
            ''')
        elif rpm > revlimit1:
            self.app.ui.rpmProgressbar.setStyleSheet('''
            QProgressBar {
                background-color: #555;
            }
            QProgressBar::chunk {background: rgb(246, 211, 45);}
            ''')
        else:
            self.app.ui.rpmProgressbar.setStyleSheet('''
            QProgressBar {
                background-color: #555;
            }
            QProgressBar::chunk {background: rgb(53, 132, 228);}
            ''')

        if self.logfile:
            data_line = ','.join([str(self.can_data[k]) for k in self.keys_to_log])
            self.logfile.write(f'{time.time()},{self.filtered_gear()},{data_line}\n')
            self.logfile.flush()
            os.fsync(self.logfile)

    def get_log_labels(cls):
        return [k for k in cls.keys_to_log] + ['gear']
    
    def get_log_data(self):
        return [str(self.can_data[k]) for k in self.keys_to_log] + [self.filtered_gear()]
        


class DataLoggableABC(ABC):

    @classmethod
    def get_log_labels(cls) -> list[str]:
        pass

    @abstractmethod
    def get_log_data(self) -> list[str]:
        pass


class DataLogger():

    def __init__(self, log_filename: str, logableclasses: list[DataLoggableABC]=[]):
        self.loggableclasses = logableclasses
        self.logging_status = False

        if os.path.exists(log_filename):
            raise Exception(f'Logfile already exists: {log_filename}')

        self.logfile = open(log_filename, 'w')
        
        labels = sum([l.get_log_labels() for l in self.loggableclasses])
        self.logfile.write(','.join(labels))

    def get_logging_status(self):
        return self.logging_status
    
    def write_log(self):
        data = sum([l.get_log_data() for l in self.loggableclasses])

        try:
            self.logfile.write(','.join(data))
            self.logfile.flush()
            os.fsync()
            self.logging_status = True

        except Exception as e:
            print(f'Exception occured during logging: {e}')
            self.logging_status = False
        



    


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(ApplicationWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

    def keyPressEvent(self, keyEvent) -> None:
        logging.info(f"Key pressed: {keyEvent.text()}")
        if keyEvent.text() == 'q':
            self.close()

def main():

    parser = argparse.ArgumentParser(
                    prog = 'Dashboard',
                    description = 'Dashboard')

    parser.add_argument('-i', '--interface', type=str, nargs=1, default='vacn0', help='CAN interface to sniff')
    parser.add_argument('-l', '--log', nargs=1, help='Logging file')
    parser.add_argument('-s', '--segments', nargs=1, help='Track sector segments')
    parser.add_argument('-m', '--microsegments', nargs=1, help='Track microsegments')

    args = parser.parse_args()

    can_decoders = [candecoder.Can200Decoder, candecoder.Can201Decoder, candecoder.Can211Decoder, \
        candecoder.Can212Decoder, candecoder.Can215Decoder, candecoder.Can231Decoder, \
        candecoder.Can240Decoder, candecoder.Can420Decoder, candecoder.Can430Decoder]
    
    app = QtWidgets.QApplication(sys.argv)
    application = ApplicationWindow()


    interface = args.i


    if args.l:
        if os.path.isfile(args.l):
            raise Exception("Log file of that name already exists")

        logfile = open(args.l, 'w')
    else:
        logfile = None

    dm = DisplayManager(can_decoders=can_decoders, qtapplication=application, logfile=logfile)

    mgr = canmanager.CanBusManager(interface, decoders=can_decoders)

    mgr.posthook = dm.get_can_update

    

    timer = QTimer(app)
    timer.setInterval(16)
    timer.setSingleShot(False)
    timer.timeout.connect(dm.update_displays)

    time.sleep(1)
    timer.start()



    application.show()
    sys.exit(app.exec_())

    

if __name__ == '__main__':
    main()