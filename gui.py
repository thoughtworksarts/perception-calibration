from enum import Enum, auto

import wx

from config import *
from models import *
from gui_events import *

# Flush output by default (it gets buffered otherwise)
import functools
print = functools.partial(print, flush=True)

proceed_image_path = os.path.join(
    os.path.dirname(__file__),
    'media',
    'Calibrate_Eye_Tracking_Proceed.png',
)

seat_adjustment_image_path = os.path.join(
    os.path.dirname(__file__),
    'media',
    'If_You_Cannot_See.png',
)

stare_image_path = os.path.join(
    os.path.dirname(__file__),
    'media',
    'Stare-at-each-dot-centered.png',
)

class CalibrationMode(Enum):
    POSITIONING_USER = auto()
    CALIBRATING_EYES = auto()
    FINALIZING_CALIBRATION = auto()
    CALIBRATION_CONCLUDED = auto()

class CalibrationFrame(wx.Frame):
    def __init__(self, parent=None, title='Eye-Tracking Calibration', debug=False):
        self.debug = debug
        self.mode = None

        wx.Frame.__init__(self, parent, title=title, size=(200, 100))

        self.to_proceed_bitmap = wx.Bitmap(proceed_image_path)
        self.seat_adjustment_bitmap = wx.Bitmap(seat_adjustment_image_path)
        self.stare_bitmap = wx.Bitmap(stare_image_path)

        self.current_point = None
        self.user_position_guide = None

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_UP, self.CloseFrame)
        self.Bind(EVT_CALIBRATION, self.OnCalibration)
        self.Bind(EVT_CLOSE_APP, self.CloseFrame)

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
        if event.calibration_event_type == CALIBRATION_CONCLUDED:
            self.mode = CalibrationMode.CALIBRATION_CONCLUDED
            self.Close()
        elif event.calibration_event_type == FINALIZING_CALIBRATION:
            self.mode = CalibrationMode.FINALIZING_CALIBRATION
        elif event.calibration_event_type == SHOW_POINT:
            self.mode = CalibrationMode.CALIBRATING_EYES
            self.current_point = event.point
            self.success_count = event.success_count
        elif event.calibration_event_type == UPDATE_USER_POSITION:
            self.mode = CalibrationMode.POSITIONING_USER
            self.user_position_guide = event.user_position_guide

        # Force a redraw
        self.Refresh(eraseBackground=ERASE_BACKGROUND)
        self.Update()

    def CloseFrame(self, event):
        print(f"Closing Frame ({self.__class__.__name__})")
        self.Close()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)

        brush_black = wx.Brush("black")

        dc.SetBackground(brush_black)
        dc.Clear()

        display_width, display_height = wx.DisplaySize()

        if self.mode == CalibrationMode.POSITIONING_USER:
            self.DrawUserPositionInstructions(dc, display_width, display_height)
            self.DrawUserPositionGuide(dc, display_width, display_height)
        elif self.mode == CalibrationMode.CALIBRATING_EYES:
            self.DrawCalibrationPoints(dc, display_width, display_height, self.success_count)
        elif self.mode == CalibrationMode.FINALIZING_CALIBRATION:
            self.DrawFinalizingCalibration(dc, display_width, display_height)

        if self.debug:
            self.DrawConfigDebugInfo(dc, display_width, display_height)

    def DrawFinalizingCalibration(self, dc, display_width, display_height):
        text = 'Finalizing calibration'

        dc.SetTextForeground("blue")
        dc.DrawText(text=text, x=10, y=10)

    def DrawUserPositionInstructions(self, dc, display_width, display_height):
        instruction_margin = 40

        dc.DrawBitmap(
            bitmap=self.to_proceed_bitmap,
            x=instruction_margin,
            y=instruction_margin,
            useMask=False,
        )

        seat_x = display_width - self.seat_adjustment_bitmap.GetWidth() - instruction_margin
        seat_y = display_height - self.seat_adjustment_bitmap.GetHeight() - instruction_margin

        dc.DrawBitmap(
            bitmap=self.seat_adjustment_bitmap,
            x=seat_x,
            y=seat_y,
            useMask=False,
        )

    def DrawUserPositionGuide(self, dc, display_width, display_height):
        display = Display(
            context=dc,
            width=display_width,
            height=display_height,
        )

        self.DrawUserFaceTarget(display)

        self.DrawUserFace(display, self.user_position_guide)

        self.DrawUserFaceScore(display, self.user_position_guide.score)

        if self.debug:
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

    def DrawUserFace(self, display, user_position_guide):
        left_user_position = user_position_guide.left_position
        right_user_position = user_position_guide.right_position

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
        bar_width = 100
        bar_height = 20

        center_x = display.width / 2
        center_y = display.height / 2

        bar_x = center_x - (bar_width / 2)
        bar_y = center_y + 300  # TODO: Derive from face radius

        # TODO: Purposefully draw the progress bar as the mouth?

        # Progress bar
        display.context.SetPen(wx.Pen("white"))
        display.context.SetBrush(wx.Brush("green"))

        progress_height = bar_height
        progress_width = bar_width * score
        progress_x = center_x - (progress_width / 2) # TODO: Center properly
        progress_y = bar_y

        display.context.DrawRectangle(
            progress_x,
            progress_y,
            progress_width,
            bar_height,
        )

        # Frame around progress bar
        display.context.SetPen(wx.Pen("white", 3))
        display.context.SetBrush(wx.Brush("black", style=wx.TRANSPARENT))

        display.context.DrawRectangle(bar_x, bar_y, bar_width, bar_height)

    def DrawUserFaceDebugInfo(self, display):
        score = self.user_position_guide.score

        score_text = f"Head Position Score: {score}\n"

        left = self.user_position_guide.left_position
        right = self.user_position_guide.right_position

        left_text = f"L: ({left.x:0.4f}) ({left.y:0.4f}) ({left.z:0.4f})"
        right_text = f"L: ({right.x:0.4f}) ({right.y:0.4f}) ({right.z:0.4f})"

        text = "\n".join([score_text, left_text, right_text])

        display.context.SetTextForeground("white")
        display.context.DrawText(text=text, x=10, y=10)

    def DrawCalibrationPoints(self, dc, display_width, display_height, success_count):
        stare_x = (display_width / 2) - (self.stare_bitmap.GetWidth() / 2)
        stare_y = (display_height / 2) - (self.stare_bitmap.GetHeight() / 2) - 120

        dc.DrawBitmap(
            bitmap=self.stare_bitmap,
            x=stare_x,
            y=stare_y,
            useMask=False,
        )

        dc.SetBrush(wx.Brush("blue"))

        if self.current_point in self.point_mapping:
            # Shrink the circle as successes accumulate
            radius = CIRCLE_RADIUS * (1 - (success_count / DOT_RESULT_SUCCESSES_REQUIREMENT))

            self.point_mapping[self.current_point](
                dc,
                display_width,
                display_height,
                radius
            )

    def DrawCenterCircle(self, dc, display_width, display_height, radius):
        x = display_width / 2
        y = display_height / 2

        dc.DrawCircle(x, y, radius)

    def DrawUpperLeftCircle(self, dc, display_width, display_height, radius):
        x = CIRCLE_MARGIN + CIRCLE_RADIUS
        y = CIRCLE_MARGIN + CIRCLE_RADIUS

        dc.DrawCircle(x, y, radius)

    def DrawUpperRightCircle(self, dc, display_width, display_height, radius):
        x = display_width - CIRCLE_MARGIN - CIRCLE_RADIUS
        y = CIRCLE_MARGIN + CIRCLE_RADIUS

        dc.DrawCircle(x, y, radius)

    def DrawLowerLeftCircle(self, dc, display_width, display_height, radius):
        x = CIRCLE_MARGIN + CIRCLE_RADIUS
        y = display_height - CIRCLE_MARGIN - CIRCLE_RADIUS

        dc.DrawCircle(x, y, radius)

    def DrawLowerRightCircle(self, dc, display_width, display_height, radius):
        x = display_width - CIRCLE_MARGIN - CIRCLE_RADIUS
        y = display_height - CIRCLE_MARGIN - CIRCLE_RADIUS

        dc.DrawCircle(x, y, radius)

    def DrawConfigDebugInfo(self, dc, display_width, display_height):
        config_text = ''

        for config_name in constants_and_defaults:
            config_text += f"{config_name} = {globals()[config_name]}\n"

        config_text += "Current Mode: {self.mode}"

        # TODO: Why is the text width so large?
        text_width, text_height = dc.GetTextExtent(config_text)

        text_width = 350  # TODO: Replace with dynamic text width

        x = display_width - text_width - 10
        y = 10

        dc.SetTextForeground("white")
        dc.DrawText(text=config_text, x=x, y=y)
