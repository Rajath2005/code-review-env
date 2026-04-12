"""Strict open-interval (0, 1) score clamping for validator safety."""


def clamp_score(score):
    try:
        score = float(score)
    except (TypeError, ValueError):
        return 0.01

    if score != score:  # NaN
        return 0.01

    if score <= 0.01:
        return 0.01
    if score >= 0.99:
        return 0.99

    return score
