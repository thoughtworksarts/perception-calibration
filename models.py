from enum import Enum, auto

class Display:
    def __init__(self, context, width, height):
        self.context = context
        self.width = width
        self.height = height

class UserPosition:
    def __init__(self, x, y, z, valid):
        self.x = x
        self.y = y
        self.z = z
        self.valid = valid

class UserPositionGuide:
    def __init__(self, left_position=None, right_position=None):
        self.left_position = left_position
        self.right_position = right_position

        self.score = 0  # TODO: Remove

    def to_dict(self):
        guide = {}

        if self.left_position:
            left_validity = self.left_position.valid and 1 or 0
            guide['left_user_position_validity'] = left_validity
            guide['left_user_position'] = (
                self.left_position.x,
                self.left_position.y,
                self.left_position.z,
            )
        else:
            guide['left_user_position_validity'] = 0
            guide['left_user_position'] = (
                math.nan,
                math.nan,
                math.nan,
            )

        if self.right_position:
            right_validity = self.right_position.valid and 1 or 0
            guide['right_user_position_validity'] = right_validity
            guide['right_user_position'] = (
                self.right_position.x,
                self.right_position.y,
                self.right_position.z,
            )
        else:
            guide['right_user_position_validity'] = 0
            guide['right_user_position'] = (
                math.nan,
                math.nan,
                math.nan,
            )

        guide['score'] = self.score

        return guide

    @staticmethod
    def from_dict(guide_dict):
        left_guide = guide_dict['left_user_position']
        left_valid = guide_dict['left_user_position_validity'] == 1

        left_user_position = UserPosition(
            x=left_guide[0],
            y=left_guide[1],
            z=left_guide[2],
            valid=left_valid,
        )

        right_guide = guide_dict['right_user_position']
        right_valid = guide_dict['right_user_position_validity'] == 1

        right_user_position = UserPosition(
            x=right_guide[0],
            y=right_guide[1],
            z=right_guide[2],
            valid=right_valid,
        )

        return (left_user_position, right_user_position)

class PointLocation(Enum):
    CENTER = (0.5, 0.5)
    UPPER_LEFT = (0.1, 0.1)
    UPPER_RIGHT = (0.1, 0.9)
    LOWER_LEFT = (0.9, 0.1)
    LOWER_RIGHT =(0.9, 0.9)

