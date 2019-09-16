import argparse

from eyetrackers import TobiiEyeTracker, FakeEyeTracker

from calibration_app import CalibrationApp

# Flush output by default (it gets buffered otherwise)
import functools
print = functools.partial(print, flush=True)

parser = argparse.ArgumentParser()
parser.add_argument(
    '--simulate-success',
    action='store_true',
    help='If true, exit with a success without attempting calibration',
)
args = parser.parse_args()

if args.simulate_success:
    eyetracker_class = FakeEyeTracker
else:
    eyetracker_class = TobiiEyeTracker

app = CalibrationApp(eyetracker_class=eyetracker_class)
app.start()
