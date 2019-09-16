from enum import Enum, auto
from random import randint
import argparse
import time
import threading
import wx

import tobii_research as tr
from tobii_research import find_all_eyetrackers

import functools
# Flush output by default (it gets buffered otherwise)
print = functools.partial(print, flush=True)

# Weights should sum up to 1.0
X_SCORE_WEIGHT = 0.4
Y_SCORE_WEIGHT = 0.4
Z_SCORE_WEIGHT = 0.2

CIRCLE_MARGIN = 20
CIRCLE_RADIUS = 20

EVT_TYPE_CALIBRATION = wx.NewEventType()
EVT_CALIBRATION = wx.PyEventBinder(EVT_TYPE_CALIBRATION)

class Display:
    def __init__(self, context, width, height):
        self.context = context
        self.width = width
        self.height = height

class UserPosition:
    def __init__(self, x, y, z, valid):
        self.x = x
        self.y = y
        self.z = z
        self.valid = valid

class UserPositionScorer:
    def __init__(self):
        self.recent_positions = []
        self.positions_range = 100  # Arbitrary threshold. TODO: Test

    def add_positions(self, user_positions):
        if len(self.recent_positions) < self.positions_range:
            self.recent_positions.append(user_positions)
        else:
            self.recent_positions.pop(0)
            self.recent_positions.append(user_positions)

    def calculate_total_score(self):
        total_score = 0

        for positions in self.recent_positions:
            total_score += self.calculate_score_for_positions(positions)

        return total_score / self.positions_range

    def calculate_score_for_positions(self, positions):
        left_score = self.calculate_score_for_position(positions.left_position)

        if left_score == 0:
            return 0

        right_score = self.calculate_score_for_position(positions.right_position)

        if right_score == 0:
            return 0

        return (left_score + right_score)

    def calculate_score_for_position(self, position):
        if not position.valid:
            return 0

        x_score = abs(position.x) * X_SCORE_WEIGHT
        y_score = abs(position.y) * Y_SCORE_WEIGHT
        z_score = abs(position.z) * Z_SCORE_WEIGHT

        return (x_score + y_score + z_score)

class UserPositions:
    def __init__(self, left_position=None, right_position=None):
        self.left_position = left_position
        self.right_position = right_position

        self.score = 0  # TODO: Remove

    def to_guide(self):
        guide = {}

        if self.left_position:
            left_validity = self.left_position.valid and 1 or 0
            guide['left_user_position_validity'] = left_validity
            guide['left_user_position'] = (
                self.left_position.x,
                self.left_position.y,
                self.left_position.z,
            )
        else:
            guide['left_user_position_validity'] = 0
            guide['left_user_position'] = (
                math.nan,
                math.nan,
                math.nan,
            )

        if self.right_position:
            right_validity = self.right_position.valid and 1 or 0
            guide['right_user_position_validity'] = right_validity
            guide['right_user_position'] = (
                self.right_position.x,
                self.right_position.y,
                self.right_position.z,
            )
        else:
            guide['right_user_position_validity'] = 0
            guide['right_user_position'] = (
                math.nan,
                math.nan,
                math.nan,
            )

        guide['score'] = self.score

        return guide

    @staticmethod
    def from_user_position_guide(guide):
        left_guide = guide['left_user_position']
        left_valid = guide['left_user_position_validity'] == 1

        left_user_position = UserPosition(
            x=left_guide[0],
            y=left_guide[1],
            z=left_guide[2],
            valid=left_valid,
        )

        right_guide = guide['right_user_position']
        right_valid = guide['right_user_position_validity'] == 1

        right_user_position = UserPosition(
            x=right_guide[0],
            y=right_guide[1],
            z=right_guide[2],
            valid=right_valid,
        )

        return (left_user_position, right_user_position)

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
            exit(0)
        except Exception as e:
            import traceback
            print("Unable to initiate calibration:")
            print(f"Error: {e}")
            traceback.print_exc()
            exit(1)

class FakeEyeTracker:
    """
    For testing GUI integration in the absence of an actual Tobii device
    """

    def __init__(self, gui):
        self.gui = gui

        # Tracks how well the user's head has been positioned
        self.user_position_score = 0

    def calibrate(self):
        self.simulate_user_position_calibration()
        self.simulate_eye_point_calibration()

        wx.PostEvent(self.gui, CalibrationConcludedEvent())

    def simulate_user_position_calibration(self):
        left_position = UserPosition(x=0.44, y=0.5, z=0.5, valid=True)
        right_position = UserPosition(x=0.56, y=0.5, z=0.5, valid=True)
        user_positions = UserPositions(left_position, right_position)

        scorer = UserPositionScorer()
        scorer.add_positions(user_positions)

        for _ in range(5000):
            left_position, right_position = \
                self.apply_random_head_step(left_position, right_position)

            user_positions = UserPositions(left_position, right_position)

            scorer.add_positions(user_positions)

            score = scorer.calculate_total_score()

            fake_guide = user_positions.to_guide()

            fake_guide['score'] = score

            wx.PostEvent(self.gui, UpdateUserPositionEvent(fake_guide))
            time.sleep(0.02)

    def apply_random_head_step(self, left_position, right_position):
        x_adjust = randint(-1, 1) / 500
        y_adjust = randint(-1, 1) / 500
        z_adjust = randint(-1, 1) / 500

        left_position.x += x_adjust
        left_position.y += y_adjust
        #left_position.z += z_adjust

        right_position.x += x_adjust
        right_position.y += y_adjust
        #right_position.z += z_adjust

        return (left_position, right_position)

    def simulate_eye_point_calibration(self):
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

            time.sleep(0.3)

        wx.PostEvent(self.gui, ShowPointEvent(None))

class MyEyeTracker:
    def __init__(self, gui):
        self.gui = gui
        self.user_position_score = 0  # Tracks how well the user's head has been positioned

        trackers = find_all_eyetrackers()

        if (len(trackers) == 0):
            raise Exception("No tracker available")

        self.eyetracker = trackers[0]

    def calibrate_user_position(self):
        def callback(user_position_guide):
            guide_with_score = copy.copy(user_position_guide)
            guide_with_score['score'] = self.user_position_score

            wx.PostEvent(self.gui, UpdateUserPositionEvent(user_position_guide))

        print("Subscribing to user position guide")
        self.eyetracker.subscribe_to(tr.EYETRACKER_USER_POSITION_GUIDE, callback, as_dictionary=True)

        time.sleep(60)

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
        self.user_position_guide = None

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
        if event.calibration_event_type == UPDATE_USER_POSITION:
            self.user_position_guide = event.user_position_guide

            # Force a redraw
            self.Refresh()
            self.Update()
        if event.calibration_event_type == CALIBRATION_CONCLUDED:
            self.Close()

    def CloseFrame(self, event):
        self.Close()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)

        brush_black = wx.Brush("black")

        dc.SetBackground(brush_black)
        dc.Clear()

        display_width, display_height = wx.DisplaySize()

        if self.current_point:
            self.DrawCalibrationPoints(dc, display_width, display_height)
        elif self.user_position_guide:
            self.DrawUserPositionGuide(dc, display_width, display_height)

    def DrawUserPositionGuide(self, dc, display_width, display_height):
        display = Display(
            context=dc,
            width=display_width,
            height=display_height,
        )

        left_user_position, right_user_position = \
            UserPositions.from_user_position_guide(self.user_position_guide)

        self.DrawUserFaceTarget(display)

        self.DrawUserFace(display, left_user_position, right_user_position)

        self.DrawUserFaceScore(display, self.user_position_guide['score'])

        self.DrawUserFaceDebugInfo(display)

    def DrawUserFaceTarget(self, display):
        thickness = 8  # Arbitrary but promising guess
        radius = 50  # Arbitrary but promising guess

        pen = wx.Pen("white", width=thickness, style=wx.PENSTYLE_SHORT_DASH)

        display.context.SetPen(pen)
        display.context.SetBrush(wx.Brush("white", wx.TRANSPARENT))

        center_x = display.width / 2
        center_y = display.height / 2

        left_x = center_x - (radius * 2)
        right_x = center_x + (radius * 2)

        display.context.DrawCircle(left_x, center_y, radius)
        display.context.DrawCircle(right_x, center_y, radius)

        radius = 225  # Arbitrary but promising guess

        display.context.DrawCircle(center_x, center_y, radius)

    def DrawUserFace(self, display, left_user_position, right_user_position):
        self.DrawUserEye(display, left_user_position)
        self.DrawUserEye(display, right_user_position)

        pen = wx.Pen("green", width=3, style=wx.PENSTYLE_SOLID)

        display.context.SetPen(pen)
        display.context.SetBrush(wx.Brush("green", wx.TRANSPARENT))

        if left_user_position.valid and right_user_position.valid:
            x = (left_user_position.x + right_user_position.x) / 2
            y = (left_user_position.y + right_user_position.y) / 2
            z = (left_user_position.z + right_user_position.z) / 2

            x = x * display.width
            y = y * display.height

            radius = 450 * (1 - z) # Arbitrary guess

            display.context.DrawCircle(x, y, radius)

    def DrawUserEye(self, display, user_position):
        display.context.SetPen(wx.Pen("green", 3))
        display.context.SetBrush(wx.Brush("green", wx.TRANSPARENT))

        if user_position.valid:
            x = display.width * user_position.x
            y = display.height * user_position.y
            radius = 100 * (1 - user_position.z)

            display.context.DrawCircle(int(x), int(y), int(radius))

    def DrawUserFaceScore(self, display, score):
        # TODO: Progress bar
        pass

    def DrawUserFaceDebugInfo(self, display):
        score = self.user_position_guide['score']

        score_text = f"Head Position Score: {score}\n"

        left = self.user_position_guide['left_user_position']
        right = self.user_position_guide['right_user_position']

        left_text = f"L: ({left[0]:0.4f}) ({left[1]:0.4f}) ({left[2]:0.4f})"
        right_text = f"R: ({right[0]:0.4f}) ({right[1]:0.4f}) ({right[2]:0.4f})"

        text = "\n".join([score_text, left_text, right_text])

        display.context.SetTextForeground("white")
        display.context.DrawText(text=text, x=10, y=10)

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

parser = argparse.ArgumentParser()
parser.add_argument(
    '--simulate-success',
    action='store_true',
    help='If true, exit with a success without attempting calibration',
)
args = parser.parse_args()

app = wx.App(redirect=False)

frame = MyFrame(
    parent=None,
    title='Eye-Tracking Calibration',
)

if args.simulate_success:
    eyetracker = FakeEyeTracker(gui=frame)
else:
    eyetracker = MyEyeTracker(gui=frame)

worker = CalibrationThread(frame, eyetracker)
worker.start()

frame.ShowFullScreen(True)
frame.Show(True)

app.MainLoop()
