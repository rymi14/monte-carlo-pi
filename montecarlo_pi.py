
import argparse
import math

import numpy as np

def positive_integer(text: str) -> int:

    try:
        value = int(text)
    except ValueError as ve:
        raise argparse.ArgumentTypeError(f"`{text}` is not an integer. {ve}") from None

    if value <= 0:
        raise argparse.ArgumentTypeError("The number of points must be positive.")

    return value

def cal_pi(n: int, rng: np.random.Generator) -> float:
    x = rng.uniform(-1, 1, n)
    y = rng.uniform(-1, 1, n)

    inside = np.count_nonzero(x**2 + y**2 <= 1.0)

    return 4.0 * inside / n

n = positive_integer(input("How many points do you wish to generate? "))

rng = np.random.default_rng()
pi_est = cal_pi(n, rng)

print(f"The estimated value of π is: {pi_est:.4f}")
