import wx

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
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

app = wx.App(False)
frame = MyFrame(None, 'Eye-Tracking Calibration')
app.MainLoop()
