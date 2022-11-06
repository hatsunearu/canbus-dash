import re
import canmanager, candecoder
import pprint

import dearpygui.dearpygui as dpg
import time




class DisplayManager():

    # reference gear ratios, rpm / vss, in kph
    ref_gear_ratios = [142.91697013838305, 83.27517447657029, 59.904354392147, 42.876771767428416, 36.34426533259218, 30.183701387531755]


    def __init__(self, can_decoders):
        self._last_unstable_gear_time = 0

        self.can_data = {}

        for decoder in can_decoders:
            for field in decoder.result._fields:
                self.can_data[field] = 0

    
    def filtered_gear(self):
        # too slow, avoid division by zero
        if self.can_data['speed'] < 1:
            self._last_unstable_gear_time = time.time()
            return 'N'

        # detect stable gear ratio
        stable_ratio = None
        for i, r in enumerate(self.ref_gear_ratios):
            if 0.90 < ((self.can_data['rpm'] / self.can_data['speed']) / r) < 1.10:
                stable_ratio = i + 1
                break
        
        # no stable ratio detected, or clutched
        if not stable_ratio or self.can_data['clutch'] or self.can_data['gearneutral']: 
            self._last_unstable_gear_time = time.time()
            return 'N'

        # stable ratio detected, and time passed since last unstable
        elif time.time() - self._last_unstable_gear_time > 0.1:
            return stable_ratio
        
        # stable ratio detected, but timeout has not passed
        # don't update unstable time
        else:
            return 'N'
        
    def get_can_update(self, data, timestamp):
        for k, v in data._asdict().items():
            self.can_data[k] = v

    def update_displays(self):
        dpg.set_value('erpm_textbox', f"{self.can_data['rpm']:.0f}")
        dpg.set_value('speed_textbox', f"{abs(self.can_data['speed'] * 0.621371):.0f} mph")
        dpg.set_value('ratio_textbox', f"{self.can_data['rpm'] / self.can_data['speed']:.1f}")
        dpg.set_value('gear_textbox', self.filtered_gear())
        dpg.set_value('clutch_textbox', "CLUTCH" if self.can_data['clutch'] else "")
        dpg.set_value('ingear_textbox', "GEAR" if self.can_data['gearneutral'] else "")
        dpg.set_value('can201u1_textbox', f"{self.can_data['can201unknown1']:.0f}")



def main():

    can_decoders = [candecoder.Can201Decoder, candecoder.Can231Decoder]

    dm = DisplayManager(can_decoders=can_decoders)
    mgr = canmanager.CanBusManager('vcan0', posthook=dm.get_can_update, decoders=can_decoders)
    
    dpg.create_context()
    dpg.configure_app(init_file="dashboard_save.ini")

    with dpg.font_registry():
        font = dpg.add_font("/home/hatsu/Downloads/monaco.ttf", 64)


    viewport = dpg.create_viewport(title='Dashboard', width=640, height=480)
    dpg.setup_dearpygui()



    with dpg.theme() as container_theme:

        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (150, 100, 100), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)


    with dpg.window(label="ERPM", tag="ERPM"):
        erpm_textbox = dpg.add_text("0000", tag="erpm_textbox")
        dpg.bind_item_font(erpm_textbox, font)
        
    with dpg.window(label="Speed", tag="VSS"):
        speed_textbox = dpg.add_text("0000", tag="speed_textbox")
        dpg.bind_item_font(speed_textbox, font)
    
    with dpg.window(label="Gear Ratio", tag="GR"):
        ratio_textbox = dpg.add_text("0000", tag="ratio_textbox")
        dpg.bind_item_font(ratio_textbox, font)
    
    with dpg.window(label="Gear", tag="GEAR"):
        gear_textbox = dpg.add_text("N", tag="gear_textbox")
        dpg.bind_item_font(gear_textbox, font)
    
    with dpg.window(label="Clutch", tag="CLUTCH"):
        clutch_textbox = dpg.add_text("", tag="clutch_textbox")
        dpg.bind_item_font(clutch_textbox, font)
    
    with dpg.window(label="Gear",  tag="INNEUTRAL"):
        ingear_textbox = dpg.add_text("", tag="ingear_textbox")
        dpg.bind_item_font(ingear_textbox, font)

    with dpg.window(label="201Unknown1", tag="201Unknown1"):
        can201u1_textbox = dpg.add_text("", tag="can201u1_textbox")
        dpg.bind_item_font(can201u1_textbox, font)


    dpg.show_viewport()

    dpg.render_dearpygui_frame()

    try:
        # below replaces, start_dearpygui()
        while dpg.is_dearpygui_running():
            # insert here any code you would like to run in the render loop
            dm.update_displays()
            # you can manually stop by using stop_dearpygui()
            dpg.render_dearpygui_frame()
            

    except KeyboardInterrupt:
        dpg.save_init_file("dashboard_save.ini")
    dpg.save_init_file("dashboard_save.ini")

    dpg.destroy_context()
    

if __name__ == '__main__':
    main()