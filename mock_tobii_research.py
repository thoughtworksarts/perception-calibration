import math
import threading
import time

EYETRACKER_USER_POSITION_GUIDE = "eyetracker_user_position_guide"
CALIBRATION_STATUS_SUCCESS = "calibration_status_success"

class MockUserPositionThread(threading.Thread):
    def __init__(self, callback):
        self.callback = callback

        threading.Thread.__init__(self)

    def run(self):
        mock_guide_dict = {
            'left_user_position_validity': 1,
            'left_user_position': (0.44, 0.5, 0.5),
            'right_user_position_validity': 1,
            'right_user_position': (0.56, 0.5, 0.5),
        }

        for _ in range(5000):
            self.callback(mock_guide_dict)
            time.sleep(0.02)

class MockEyeTracker:
    """
    Drop-in replacement for tobii_research.EyeTracker
    """
    def __init__(self):
        self.serial_number = "MOCK SERIAL NUMBER"

    def subscribe_to(self, guide, callback, as_dictionary=True):
        worker = MockUserPositionThread(callback)
        worker.start()

    def unsubscribe_from(self, guide, callback):
        pass

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
        return "calibration_status_success"

    def compute_and_apply(self):
        return MockCalibrationResult()

def find_all_eyetrackers():
    return [MockEyeTracker()]
