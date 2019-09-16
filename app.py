from enum import Enum, auto
import argparse
import threading
import wx

import tobii_research as tr
from tobii_research import find_all_eyetrackers

import functools
# Flush output by default (it gets buffered otherwise)
print = functools.partial(print, flush=True)

from constants import *
from models import *
from gui import *

from eyetrackers import TobiiEyeTracker, FakeEyeTracker

class CalibrationThread(threading.Thread):
    def __init__(self, parent, eyetracker):
        self.parent = parent
        self.eyetracker = eyetracker

        threading.Thread.__init__(self)

    def run(self):
        print("Initiating calibration")
        try:
            self.eyetracker.calibrate()
            print("Calibration process concluded")
            exit(0)
        except Exception as e:
            import traceback
            print("Unable to initiate calibration:")
            print(f"Error: {e}")
            traceback.print_exc()
            exit(1)

class CalibrationApp:
    def __init__(self, args):
        self.args = args

    def start(self):
        wx_app = wx.App(redirect=False)

        frame = CalibrationFrame()

        if self.args.simulate_success:
            eyetracker = FakeEyeTracker(gui=frame)
        else:
            eyetracker = TobiiEyeTracker(gui=frame)

        worker = CalibrationThread(frame, eyetracker)
        worker.start()

        frame.ShowFullScreen(True)
        frame.Show(True)

        wx_app.MainLoop()

parser = argparse.ArgumentParser()
parser.add_argument(
    '--simulate-success',
    action='store_true',
    help='If true, exit with a success without attempting calibration',
)

app = CalibrationApp(parser.parse_args())
app.start()
