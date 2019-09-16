import wx

USER_POSITION_SCORE_REQUIREMENT = 0.85  # 1.0 = perfect aligment

# How many previous scores to sum up when calculating total score
USER_POSITION_SCORE_BACK_LOOK = 100  # Arbitrary threshold. TODO: Test

# Weights should sum up to 1.0
X_SCORE_WEIGHT = 0.4
Y_SCORE_WEIGHT = 0.4
Z_SCORE_WEIGHT = 0.2

# Scores shrink expontentially worse the farther the head is off target
X_SCORE_EXPONENT = 10
Y_SCORE_EXPONENT = 10
Z_SCORE_EXPONENT = 10

CIRCLE_MARGIN = 20
CIRCLE_RADIUS = 20
