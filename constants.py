import wx

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
