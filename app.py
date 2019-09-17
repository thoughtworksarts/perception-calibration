import argparse

from calibration_app import CalibrationApp

# Flush output by default (it gets buffered otherwise)
import functools
print = functools.partial(print, flush=True)

parser = argparse.ArgumentParser()
parser.add_argument(
    '--simulate-tobii',
    action='store_true',
    help='Use mock Tobii API (simulates data in the absence of actual hardware)',
)
parser.add_argument(
    '--debug',
    action='store_true',
    help='Enables debug mode (increased, more detailed reporting)',
)
args = parser.parse_args()

if args.simulate_tobii:
    import mock_tobii_research as tobii_api
else:
    import tobii_research as tobii_api

app = CalibrationApp(api=tobii_api, debug=args.debug)
app.start()
