from random import randint
import time

from constants import *
from models import *
from gui_events import *

# Flush output by default (it gets buffered otherwise)
import functools
print = functools.partial(print, flush=True)

class UserPositionScorer:
    def __init__(self):
        self.recent_positions = []
        self.positions_range = 100  # Arbitrary threshold. TODO: Test

    def add_positions(self, guide):
        if len(self.recent_positions) < self.positions_range:
            self.recent_positions.append(guide)
        else:
            self.recent_positions.pop(0)
            self.recent_positions.append(guide)

    def calculate_total_score(self):
        total_score = 0

        for positions in self.recent_positions:
            total_score += self.calculate_score_for_positions(positions)

        return total_score / self.positions_range

    def calculate_score_for_positions(self, positions):
        left = positions.left_position
        right = positions.right_position

        if not left.valid or not right.valid:
            return 0

        x_score = ((left.x + right.x) ** X_SCORE_EXPONENT) * X_SCORE_WEIGHT
        y_score = ((left.y + right.y) ** Y_SCORE_EXPONENT) * Y_SCORE_WEIGHT
        z_score = ((left.z + right.z) ** Z_SCORE_EXPONENT) * Z_SCORE_WEIGHT

        score_sum = x_score + y_score + z_score

        # print(f"{x_score} {y_score} {z_score}")

        return 1 - abs(1 - score_sum)

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
        guide = UserPositionGuide(left_position, right_position)

        scorer = UserPositionScorer()
        scorer.add_positions(guide)

        for _ in range(5000):
            left_position, right_position = \
                self.apply_random_head_step(left_position, right_position)

            guide = UserPositionGuide(left_position, right_position)

            scorer.add_positions(guide)

            score = scorer.calculate_total_score()

            if score > 0.85:
                return

            guide.score = score

            wx.PostEvent(self.gui, UpdateUserPositionEvent(guide))
            time.sleep(0.02)

    def apply_random_head_step(self, left_position, right_position):
        x_adjust = randint(-1, 1) / 500
        y_adjust = randint(-1, 1) / 500
        z_adjust = randint(-1, 1) / 500

        left_position.x += x_adjust
        left_position.y += y_adjust
        left_position.z += z_adjust

        right_position.x += x_adjust
        right_position.y += y_adjust
        right_position.z += z_adjust

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

class TobiiEyeTracker:
    """
    Interface to a real Tobii eye tracker device
    """

    def __init__(self, api, gui):
        self.api = api
        self.gui = gui
        self.user_position_score = 0  # Tracks how well the user's head has been positioned

        trackers = self.api.find_all_eyetrackers()

        if (len(trackers) == 0):
            raise Exception("No tracker available")

        self.eyetracker = trackers[0]

    def calibrate_user_position(self):
        scorer = UserPositionScorer()

        def callback(user_position_guide_dict):
            guide = UserPositionGuide.from_dict(user_position_guide_dict)
            scorer.add_positions(guide)

            score = scorer.calculate_total_score()

            self.user_position_score = score
            guide.score = score

            wx.PostEvent(self.gui, UpdateUserPositionEvent(guide))

        print("Subscribing to user position guide")
        self.eyetracker.subscribe_to(self.api.EYETRACKER_USER_POSITION_GUIDE, callback, as_dictionary=True)

        while True:
            time.sleep(0.02)
            if self.user_position_score > 0.85:
                break

        self.eyetracker.unsubscribe_from(self.api.EYETRACKER_USER_POSITION_GUIDE, callback)
        print("Unsubscribed from user position guide")

    def calibrate(self):
        eyetracker = self.eyetracker

        self.calibrate_user_position()

        calibration = self.api.ScreenBasedCalibration(eyetracker)

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
                if result == self.api.CALIBRATION_STATUS_SUCCESS:
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
