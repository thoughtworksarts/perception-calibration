import wx

from tobii_research import find_all_eyetrackers

class MyEyeTracker:
    def __init__(self):
        trackers = find_all_eyetrackers()

        if (len(trackers) == 0):
            raise Exception("No tracker available")

        self.eyetracker = trackers[0]

class MyFrame(wx.Frame):
    def __init__(self, parent, title, eye_tracker):
        self.eye_tracker = eye_tracker

        wx.Frame.__init__(self, parent, title=title, size=(200, 100))

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_UP, self.CloseFrame)

        self.ShowFullScreen(True)
        self.Show(True)

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

app = wx.App(False)

frame = MyFrame(
    parent=None,
    title='Eye-Tracking Calibration',
    eye_tracker=eyetracker,
)

app.MainLoop()
