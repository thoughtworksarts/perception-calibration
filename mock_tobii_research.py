import math
from random import randint
import threading
import time

from models import UserPosition

EYETRACKER_USER_POSITION_GUIDE = "eyetracker_user_position_guide"
CALIBRATION_STATUS_SUCCESS = "calibration_status_success"

class MockUserPositionThread(threading.Thread):
    def __init__(self, callback):
        self.callback = callback
        self.keep_running = True

        threading.Thread.__init__(self)

    def run(self):
        left_position = UserPosition(x=0.44, y=0.5, z=0.5, valid=True)
        right_position = UserPosition(x=0.56, y=0.5, z=0.5, valid=True)

        for _ in range(100_000_000):
            if not self.keep_running:
                return

            left_position, right_position = \
                self.apply_random_head_step(left_position, right_position)

            mock_guide_dict = {
                'left_user_position_validity': 1,
                'left_user_position': (left_position.x, left_position.y, left_position.z),
                'right_user_position_validity': 1,
               'right_user_position': (right_position.x, right_position.y, right_position.z),
            }

            self.callback(mock_guide_dict)
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

class MockEyeTracker:
    """
    Drop-in replacement for tobii_research.EyeTracker
    """
    def __init__(self):
        self.serial_number = "MOCK SERIAL NUMBER"

    def subscribe_to(self, guide, callback, as_dictionary=True):
        self.worker = MockUserPositionThread(callback)
        self.worker.start()

    def unsubscribe_from(self, guide, callback):
        self.worker.keep_running = False

class MockCalibrationResult:
    def __init__(self):
        self.status = "calibration_status_success"
        self.calibration_points = ((0.5, 0.5),)

class ScreenBasedCalibration:
    def __init__(self, eyetracker):
        pass

    def enter_calibration_mode(self):
        pass

    def leave_calibration_mode(self):
        pass

    def collect_data(self, x, y):
        # Succeeds more often than not
        if randint(0, 3) == 0:
            return "calibration_status_failure"
        else:
            return "calibration_status_success"

    def compute_and_apply(self):
        time.sleep(1)  # Simulate finalization of calibration
        return MockCalibrationResult()

def find_all_eyetrackers():
    return [MockEyeTracker()]
