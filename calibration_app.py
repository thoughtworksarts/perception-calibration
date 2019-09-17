import threading

import wx

from models import *
from gui import *
from gui_events import CloseAppEvent

from eyetrackers import TobiiEyeTracker

class CalibrationThread(threading.Thread):
    def __init__(self, app, parent, eyetracker):
        self.app = app
        self.parent = parent
        self.eyetracker = eyetracker

        threading.Thread.__init__(self)

    def run(self):
        print("Initiating calibration")
        try:
            self.eyetracker.calibrate()
            print("Calibration process concluded")
        except Exception as e:
            import traceback
            print("Unable to initiate calibration:")
            print(f"Error: {e}")
            traceback.print_exc()
            exit(1)

class CalibrationApp:
    def __init__(self, api, debug=False):
        self.api = api
        self.debug = debug

    def start(self):
        wx_app = wx.App(redirect=False)

        frame = CalibrationFrame(debug=self.debug)

        eyetracker = TobiiEyeTracker(api=self.api, gui=frame)

        worker = CalibrationThread(wx_app, frame, eyetracker)
        worker.start()

        frame.ShowFullScreen(True)
        frame.Show(True)

        wx_app.MainLoop()

        print("Exited main loop")

        print("Killing calibration thread")
        worker.join()
        print("Killed calibration thread")

        print(f"Exiting wxPython")
        wx.Exit()

        exit(0)
