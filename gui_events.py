from enum import Enum, auto

import wx

class CalibrationEventType(Enum):
    SHOW_POINT = auto()
    UPDATE_USER_POSITION = auto()
    FINALIZING_CALIBRATION = auto()
    CALIBRATION_CONCLUDED = auto()

SHOW_POINT = CalibrationEventType.SHOW_POINT
UPDATE_USER_POSITION = CalibrationEventType.UPDATE_USER_POSITION
FINALIZING_CALIBRATION = CalibrationEventType.FINALIZING_CALIBRATION
CALIBRATION_CONCLUDED = CalibrationEventType.CALIBRATION_CONCLUDED

EVT_TYPE_CALIBRATION = wx.NewEventType()
EVT_CALIBRATION = wx.PyEventBinder(EVT_TYPE_CALIBRATION)

EVT_TYPE_CLOSE_APP = wx.NewEventType()
EVT_CLOSE_APP = wx.PyEventBinder(EVT_TYPE_CLOSE_APP)

class CalibrationEvent(wx.PyCommandEvent):
    def __init__(self, point=None):
        wx.PyCommandEvent.__init__(self, EVT_TYPE_CALIBRATION, -1)

class CloseAppEvent(wx.PyCommandEvent):
    def __init__(self):
        wx.PyCommandEvent.__init__(self, EVT_TYPE_CLOSE_APP, -1)

class ShowPointEvent(CalibrationEvent):
    def __init__(self, point, success_count=0):
        CalibrationEvent.__init__(self)
        self.calibration_event_type = SHOW_POINT
        self.point = point
        self.success_count = success_count

class UpdateUserPositionEvent(CalibrationEvent):
    def __init__(self, user_position_guide):
        CalibrationEvent.__init__(self)
        self.calibration_event_type = UPDATE_USER_POSITION
        self.user_position_guide = user_position_guide

class FinalizingCalibrationEvent(CalibrationEvent):
    def __init__(self):
        CalibrationEvent.__init__(self)
        self.calibration_event_type = FINALIZING_CALIBRATION

class CalibrationConcludedEvent(CalibrationEvent):
    def __init__(self):
        CalibrationEvent.__init__(self)
        self.calibration_event_type = CALIBRATION_CONCLUDED
