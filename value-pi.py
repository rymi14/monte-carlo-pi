
import numpy as np

n = int(input("How many points do you wish to generate? "))

x = np.random.uniform(-1, 1, n)
y = np.random.uniform(-1, 1, n)

inside = np.sum(x**2 + y**2 <= 1)

pi = 4 * inside / n

print(f"The estimated value of π is: {pi:.4f}")
