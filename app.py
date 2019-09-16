import argparse

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
    import mock_tobii_research as tobii_api
else:
    import tobii_research as tobii_api

app = CalibrationApp(api=tobii_api)
app.start()
