from enum import Enum, auto
import time
import threading
import wx

import tobii_research as tr
from tobii_research import find_all_eyetrackers

import functools
# Flush output by default (it gets buffered otherwise)
print = functools.partial(print, flush=True)

CIRCLE_MARGIN = 20
CIRCLE_RADIUS = 20

EVT_TYPE_CALIBRATION = wx.NewEventType()
EVT_CALIBRATION = wx.PyEventBinder(EVT_TYPE_CALIBRATION)

class PointLocation(Enum):
    CENTER = (0.5, 0.5)
    UPPER_LEFT = (0.1, 0.1)
    UPPER_RIGHT = (0.1, 0.9)
    LOWER_LEFT = (0.9, 0.1)
    LOWER_RIGHT =(0.9, 0.9)

class CalibrationEventType(Enum):
    SHOW_POINT = auto()
    UPDATE_USER_POSITION = auto()
    CALIBRATION_CONCLUDED = auto()

SHOW_POINT = CalibrationEventType.SHOW_POINT
UPDATE_USER_POSITION = CalibrationEventType.UPDATE_USER_POSITION
CALIBRATION_CONCLUDED = CalibrationEventType.CALIBRATION_CONCLUDED

class CalibrationEvent(wx.PyCommandEvent):
    def __init__(self, point=None):
        wx.PyCommandEvent.__init__(self, EVT_TYPE_CALIBRATION, -1)

class ShowPointEvent(CalibrationEvent):
    def __init__(self, point):
        CalibrationEvent.__init__(self)
        self.calibration_event_type = SHOW_POINT
        self.point = point

class UpdateUserPositionEvent(CalibrationEvent):
    def __init__(self, user_position_guide):
        CalibrationEvent.__init__(self)
        self.calibration_event_type = UPDATE_USER_POSITION
        self.user_position_guide = user_position_guide

class CalibrationConcludedEvent(CalibrationEvent):
    def __init__(self):
        CalibrationEvent.__init__(self)
        self.calibration_event_type = CALIBRATION_CONCLUDED

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
        except Exception as e:
            print("Unable to initiate calibration:")
            print(e)
            self.Close()

class MyEyeTracker:
    def __init__(self, gui):
        self.gui = gui

        trackers = find_all_eyetrackers()

        if (len(trackers) == 0):
            raise Exception("No tracker available")

        self.eyetracker = trackers[0]

    def calibrate_user_position(self):
        def callback(user_position_guide):
            wx.PostEvent(self.gui, UpdateUserPositionEvent(user_position_guide))

        print("Subscribing to user position guide")
        self.eyetracker.subscribe_to(tr.EYETRACKER_USER_POSITION_GUIDE, callback, as_dictionary=True)

        time.sleep(2)

        self.eyetracker.unsubscribe_from(tr.EYETRACKER_USER_POSITION_GUIDE, callback)
        print("Unsubscribed from user position guide")

    def calibrate(self):
        eyetracker = self.eyetracker

        self.calibrate_user_position()

        calibration = tr.ScreenBasedCalibration(eyetracker)

        calibration.enter_calibration_mode()
        print("Entered calibration mode for eye tracker with serial number {0}.".format(eyetracker.serial_number))

        # Define the points on screen we should calibrate at.
        # The coordinates are normalized, i.e. (0.0, 0.0) is the upper left corner and (1.0, 1.0) is the lower right corner.
        points_to_calibrate = [
            PointLocation.CENTER,
            PointLocation.UPPER_LEFT,
            PointLocation.UPPER_RIGHT,
            PointLocation.LOWER_LEFT,
            PointLocation.LOWER_RIGHT,
        ]

        for point_enum in points_to_calibrate:
            point = point_enum.value
            print("Show a point on screen at {0}.".format(point))
            wx.PostEvent(self.gui, ShowPointEvent(point_enum))

            # Wait a little for user to focus.
            for _ in range(3):
                time.sleep(0.7)
                print("Collecting data at {0}.".format(point))
                result = calibration.collect_data(point[0], point[1])
                if result == tr.CALIBRATION_STATUS_SUCCESS:
                    break

        wx.PostEvent(self.gui, ShowPointEvent(None))

        print("Computing and applying calibration.")
        calibration_result = calibration.compute_and_apply()
        print("Compute and apply returned {0} and collected at {1} points.".
              format(calibration_result.status, len(calibration_result.calibration_points)))

        """
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
        """

        # See that you're happy with the result.

        # The calibration is done. Leave calibration mode.
        calibration.leave_calibration_mode()

        print("Left calibration mode.")

        wx.PostEvent(self.gui, CalibrationConcludedEvent())

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(200, 100))

        self.current_point = None

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_UP, self.CloseFrame)
        self.Bind(EVT_CALIBRATION, self.OnCalibration)

        self.ShowFullScreen(True)
        self.Show(True)

        self.point_mapping = {
            PointLocation.CENTER: self.DrawCenterCircle,
            PointLocation.UPPER_LEFT: self.DrawUpperLeftCircle,
            PointLocation.UPPER_RIGHT: self.DrawUpperRightCircle,
            PointLocation.LOWER_LEFT: self.DrawLowerLeftCircle,
            PointLocation.LOWER_RIGHT: self.DrawLowerRightCircle,
        }


    def OnCalibration(self, event):
        if event.calibration_event_type == SHOW_POINT:
            self.current_point = event.point

            # Force a redraw
            self.Refresh()
            self.Update()
        if event.calibration_event_type == CALIBRATION_CONCLUDED:
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
        dc.SetBrush(wx.Brush("blue"))

        if self.current_point in self.point_mapping:
            self.point_mapping[self.current_point](
                dc, display_width, display_height
            )

    def DrawCenterCircle(self, dc, display_width, display_height):
        x = display_width / 2
        y = display_height / 2

        dc.DrawCircle(x, y, CIRCLE_RADIUS)

    def DrawUpperLeftCircle(self, dc, display_width, display_height):
        x = CIRCLE_MARGIN + CIRCLE_RADIUS
        y = CIRCLE_MARGIN + CIRCLE_RADIUS

        dc.DrawCircle(x, y, CIRCLE_RADIUS)

    def DrawUpperRightCircle(self, dc, display_width, display_height):
        x = display_width - CIRCLE_MARGIN - CIRCLE_RADIUS
        y = CIRCLE_MARGIN + CIRCLE_RADIUS

        dc.DrawCircle(x, y, CIRCLE_RADIUS)

    def DrawLowerLeftCircle(self, dc, display_width, display_height):
        x = CIRCLE_MARGIN + CIRCLE_RADIUS
        y = display_height - CIRCLE_MARGIN - CIRCLE_RADIUS

        dc.DrawCircle(x, y, CIRCLE_RADIUS)

    def DrawLowerRightCircle(self, dc, display_width, display_height):
        x = display_width - CIRCLE_MARGIN - CIRCLE_RADIUS
        y = display_height - CIRCLE_MARGIN - CIRCLE_RADIUS

        dc.DrawCircle(x, y, CIRCLE_RADIUS)

app = wx.App(redirect=False)

frame = MyFrame(
    parent=None,
    title='Eye-Tracking Calibration',
)

eyetracker = MyEyeTracker(gui=frame)

worker = CalibrationThread(frame, eyetracker)
worker.start()

frame.ShowFullScreen(True)
frame.Show(True)

app.MainLoop()
