
import argparse
import math

import numpy as np

#------------------------------------------------------------------------------------------
# Theoretical constants
#------------------------------------------------------------------------------------------

REAL_PI = math.pi

# Probability that a point falls within the unit circle
#   p = area1(unit circle) / area2(square 2X2) = pi/4
PROBABILITY = REAL_PI / 4

# Each point is a Bernoulli trial: 1 if it falls inside, 0 if it does not.
# The standard deviation is sqrt(p * (1 - p)).
SIGMA_POINT = math.sqrt(PROBABILITY * (1 - PROBABILITY))

# The estimate of pi multiplies the proportion by 4, so its error is also 
# multiplied by 4:
#   error deviation = 4 * SIGMA_PUNTO / sqrt(N)
DEVIATION_CONSTANT = 4 * SIGMA_POINT

# The mean absolute error of a normal distribution is ~0.7979 times its 
# standard deviation.
# This is the constant that should appear in the "error * sqrt(N)" column.
MEAN_ERROR_CONSTANT = DEVIATION_CONSTANT * math.sqrt(2 / math.pi)


#------------------------------------------------------------------------------------------
# Exceptions
#------------------------------------------------------------------------------------------

def positive_integer(text: str) -> int:
    """
    Convert the text to an integer and verify that it is greater than zero. 

    argparse catches the exception and displays a clean message, instead of 
    letting the program crash with a traceback.
    """

    try:
        value = int(text)
    except ValueError as ve:
        raise argparse.ArgumentTypeError(f"`{text}` is not an integer. {ve}") from None

    if value <= 0:
        raise argparse.ArgumentTypeError("The number of points must be positive.")

    return value


#------------------------------------------------------------------------------------------
# Calculation of pi
#------------------------------------------------------------------------------------------

def cal_pi(n: int, rng: np.random.Generator) -> float:
    """
    Scatter n points within the square [-1, 1] x [-1, 1] and estimate pi.
    """

    x = rng.uniform(-1, 1, n)
    y = rng.uniform(-1, 1, n)

    inside = np.count_nonzero(x**2 + y**2 <= 1.0)

    return 4.0 * inside / n

n = positive_integer(input("How many points do you wish to generate? "))

rng = np.random.default_rng()
pi_est = cal_pi(n, rng)

print(f"The estimated value of π is: {pi_est:.4f}")
