import time
import wx

import tobii_research as tr
from tobii_research import find_all_eyetrackers

class MyEyeTracker:
    def __init__(self):
        trackers = find_all_eyetrackers()

        if (len(trackers) == 0):
            raise Exception("No tracker available")

        self.eyetracker = trackers[0]

    def calibrate(self):
        eyetracker = self.eyetracker
        calibration = tr.ScreenBasedCalibration(eyetracker)

        calibration.enter_calibration_mode()
        print("Entered calibration mode for eye tracker with serial number {0}.".format(eyetracker.serial_number))

        # Define the points on screen we should calibrate at.
        # The coordinates are normalized, i.e. (0.0, 0.0) is the upper left corner and (1.0, 1.0) is the lower right corner.
        points_to_calibrate = [(0.5, 0.5), (0.1, 0.1), (0.1, 0.9), (0.9, 0.1), (0.9, 0.9)]

        for point in points_to_calibrate:
            print("Show a point on screen at {0}.".format(point))

            # Wait a little for user to focus.
            time.sleep(0.7)

            print("Collecting data at {0}.".format(point))
            if calibration.collect_data(point[0], point[1]) != tr.CALIBRATION_STATUS_SUCCESS:
                # Try again if it didn't go well the first time.
                # Not all eye tracker models will fail at this point, but instead fail on ComputeAndApply.
                calibration.collect_data(point[0], point[1])

        print("Computing and applying calibration.")
        calibration_result = calibration.compute_and_apply()
        print("Compute and apply returned {0} and collected at {1} points.".
              format(calibration_result.status, len(calibration_result.calibration_points)))

        # Analyze the data and maybe remove points that weren't good.
        recalibrate_point = (0.1, 0.1)
        print("Removing calibration point at {0}.".format(recalibrate_point))
        calibration.discard_data(recalibrate_point[0], recalibrate_point[1])

        # Redo collection at the discarded point
        print("Show a point on screen at {0}.".format(recalibrate_point))
        calibration.collect_data(recalibrate_point[0], recalibrate_point[1])

        # Compute and apply again.
        print("Computing and applying calibration.")
        calibration_result = calibration.compute_and_apply()
        print("Compute and apply returned {0} and collected at {1} points.".
              format(calibration_result.status, len(calibration_result.calibration_points)))

        # See that you're happy with the result.

        # The calibration is done. Leave calibration mode.
        calibration.leave_calibration_mode()

        print("Left calibration mode.")

class MyFrame(wx.Frame):
    def __init__(self, parent, title, eyetracker):
        self.eyetracker = eyetracker

        wx.Frame.__init__(self, parent, title=title, size=(200, 100))

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_UP, self.CloseFrame)

        self.ShowFullScreen(True)
        self.Show(True)

        print("Initiating calibration")
        try:
            self.eyetracker.calibrate()
        except Exception as e:
            print("Unable to initiate calibration:")
            print(e)
            self.Close()

    def CloseFrame(self, event):
        self.Close()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)

        brush_white = wx.Brush("white")

        dc.SetBackground(brush_white)
        dc.Clear()

        display_width, display_height = wx.DisplaySize()

        self.DrawCalibrationPoints(dc, display_width, display_height)

    def DrawCalibrationPoints(self, dc, display_width, display_height):
        margin = 20
        radius = 20

        dc.SetBrush(wx.Brush("blue"))

        # Upper-left circle
        x = margin + radius
        y = margin + radius

        dc.DrawCircle(x, y, radius)

        # Upper-right circle
        x = display_width - margin - radius
        y = margin + radius

        dc.DrawCircle(x, y, radius)

        # Lower-left circle
        x = margin + radius
        y = display_height - margin - radius

        dc.DrawCircle(x, y, radius)

        # Lower-right circle
        x = display_width - margin - radius
        y = display_height - margin - radius

        dc.DrawCircle(x, y, radius)

eyetracker = MyEyeTracker()

app = wx.App(redirect=False)

frame = MyFrame(
    parent=None,
    title='Eye-Tracking Calibration',
    eyetracker=eyetracker,
)

app.MainLoop()
