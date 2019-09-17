constants_and_defaults = {
    # 1."0": perfect aligment,
    "USER_POSITION_SCORE_REQUIREMENT": 0.85,

    # How many previous scores to sum up when calculating total score
    # Arbitrary threshold. TODO: Test
    "USER_POSITION_SCORE_BACK_LOOK": 100,

    # Weights should sum up to 1.0
    "X_SCORE_WEIGHT": 0.4,
    "Y_SCORE_WEIGHT": 0.4,
    "Z_SCORE_WEIGHT": 0.2,

    # Scores shrink expontentially worse the farther the head is off target
    "X_SCORE_EXPONENT": 10,
    "Y_SCORE_EXPONENT": 10,
    "Z_SCORE_EXPONENT": 10,

    "CIRCLE_MARGIN": 20,
    "CIRCLE_RADIUS": 20,
}

for constant_name in constants_and_defaults:
    default = constants_and_defaults[constant_name]

    globals()[constant_name] = default
