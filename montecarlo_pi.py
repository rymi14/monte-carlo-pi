
import argparse
import json
import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

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
    EXCEPTION
    
    Convert the text to an integer and verify that it is greater than zero. 

    argparse catches the exception and displays a clean message, instead of 
    letting the program crash with a traceback.
    """

    try:
        """
        Exception for a non-integer value or string.
        """
        value = int(text)
    except ValueError as ve:
        raise argparse.ArgumentTypeError(f"`{text}` is not an integer. {ve}") from None

    if value <= 0:
        """
        Exception for a negative integer.
        """
        raise argparse.ArgumentTypeError("The number of points must be positive.")

    return value


#------------------------------------------------------------------------------------------
# Data entry
#------------------------------------------------------------------------------------------
N_DEFAULT = [100, 400, 1_600, 6_400, 25_600, 102_400]
DEFAULT_REPETITIONS = 100
DEFAULT_CONVERGENCE = 100_000

def ask_integer(text: str, default: int, info: str) -> int:
    print(info)
    while True:
        answer = input(text).strip()
        if not answer:
            return default
        try:
            return positive_integer(answer)
        except argparse.ArgumentTypeError as exc:
            print(f"    {exc}. Try again.")


def ask_list(text: str, default: list[int], info: str) -> list[int]:
    print(info)
    while True:
        answer = input(text).strip()
        if not answer:
            return default
        try:
            values = [positive_integer(p) for p in answer.split()]
        except argparse.ArgumentTypeError as exc:
            print(f"    {exc}. Try again.")
        else:
            return values


def ask_seed(text: str, info: str) -> int | None:
    print(info)
    while True:
        answer = input(text).strip()
        if not answer:
            return None
        try:
            return int(answer)
        except ValueError:
            print("     It is not an integer. Try again.")

def ask_yes_no(text: str, info: str) -> bool:
    print(info)
    while True:
        answer = input(text).strip().lower()
        if answer in ("Y", "y", "Yes", "yes"):
            return True
        if answer in ("", "N", "n", "No", "no"):
            return False
        print("     Writes 'y' or 'n'.")


def fill_missing(args: argparse.Namespace) -> argparse.Namespace:
    missing = [
        args.n is None,
        args.repetitions is None,
        args.convergence is None,
        args.seed is None,
        args.save is None
    ]
    if not any(missing):
        return args

    if not sys.stdin.isatty():
        args.n = args.n or N_DEFAULT
        args.repetitions = args.repetitions or DEFAULT_REPETITIONS
        args.convergence = args.convergence or DEFAULT_CONVERGENCE
        args.save = bool(args.save)
        return args

    print()
    print("  Values ​​not defined in the terminal.")
    print("  Press Enter to accept the value in brackets.")
    print()

    if args.n is None:
        args.n = ask_list(
            "   N values ​​for the table ["
            f"{' '.join(f'{v:,}' for v in N_DEFAULT)}]: ",
            N_DEFAULT,
            info=(
                "  N from the law 1/sqrt(N).\n" 
                "    Each number represents a separate set of points. Several\n" 
                "    sizes are tested to see how the error decreases as the number\n" 
                "    of points increases. Enter them separated by spaces."
            )
        )


    if args.repetitions is None:
        args.repetitions = ask_integer(
            f"  Repetitions per value of N [{DEFAULT_REPETITIONS}]: ",
            DEFAULT_REPETITIONS,
            info=(
                "  N repetitions.\n" 
                "    A single trial depends on luck: the error can turn out\n" 
                "    to be very large or very small. By repeating the process\n" 
                "    and calculating the average, the underlying law emerges,\n" 
                "    rather than mere chance."
            )
        )


    if args.convergence is None:
        args.convergence = ask_integer(
            f"  Points on the curve"
            f"[{DEFAULT_CONVERGENCE:,}]: ",
            DEFAULT_CONVERGENCE,
            info=(
                "  Points on the convergence curve.\n" 
                "    These are run in succession, and the error is recorded\n" 
                "    each time a point is reached, in order to plot on the\n" 
                "    graph how it decreases."
            )
        )


    if args.seed is None:
        args.seed = ask_seed(
            "      Seed                     [random]: ",
            info=(
                "  Random number generator seed.\n" 
                "    A specific number determines the outcome: the results\n" 
                "    are always the same, allowing the experiment to be repeated.\n" 
                "    Enter = a different outcome each time."
            )
        )


    if args.save is None:
        args.save = ask_yes_no(
            "   Save JSON results?   [n]:",
            info=(
                "  Save the results?\n" 
                "    Write the numbers to files in the 'results/' directory. Then,\n" 
                "    'graficar.py' reads them to generate the plots."
            )
        )
    return args


#------------------------------------------------------------------------------------------
# Calculation of pi
#------------------------------------------------------------------------------------------

@dataclass
class SampleLaw:
    n: int
    estimate: float
    error: float
    theoretical_error: float
    error_for_sqr_n: float


def cal_pi(n: int, rng: np.random.Generator) -> float:
    """
    Scatter n points within the square [-1, 1] x [-1, 1] and estimate pi.
    """

    x = rng.uniform(-1.0, 1.0, n)
    y = rng.uniform(-1.0, 1.0, n)

    inside = np.count_nonzero(x * x + y * y <= 1.0)

    return 4.0 * inside / n

def theoretical_error(n: int) -> float:
    """
    Expected mean absolute error for n points, following the 1/sqrt(N) law.
    """
    return MEAN_ERROR_CONSTANT / math.sqrt(n)


def law_table(
    n_values: list[int],
    repetitions: int,
    rng: np.random.Generator
) -> list[SampleLaw]:
    """
    Repeat the experiment for each N and average the errors. 
    
    Averaging is essential: Monte Carlo is stochastic, so a single run 
    could turn out exceptionally well or poorly. The 1/sqrt(N) law refers 
    to the *average* error, not to any individual run.
    """
    
    sample = []

    for n in n_values:
        estimates = [cal_pi(n, rng) for _ in range(repetitions)]
        errors = [abs(e - REAL_PI) for e in estimates]

        mean_error = sum(errors) / len(errors)

        sample.append(
            SampleLaw(
                n=n,
                estimate=sum(estimates) / len(estimates),
                error=mean_error,
                theoretical_error=theoretical_error(n),
                error_for_sqr_n=mean_error * math.sqrt(n),
            )
        )
    return sample

def convergence_curve(
    n_total: int,
    batch_size: int, 
    rng: np.random.Generator
) -> tuple[list[int], list[float]]:
    
    x = rng.uniform(-1.0, 1.0, n_total)
    y = rng.uniform(-1.0, 1.0, n_total)

    inside = (x * x + y * y <= 1.0).astype(np.int64)
    accumulated = np.cumsum(inside)

    points = np.arange(1, n_total + 1)
    estimates = 4.0 * accumulated / points

    if batch_size > 0:
        indexes = np.unique(
            np.unique(
                np.geomspace(10, n_total, num=400, dtype=int)
            )
            // batch_size * batch_size
            - 1
        )
    else:
        indexes = np.arange(0, n_total)

    indexes = indexes[(indexes >= 0) & (indexes < n_total)]

    indexes =  np.unique(np.append(indexes, n_total - 1))

    return (
        [int(i) + 1 for i in indexes],
        [float(v) for v in estimates[indexes]]
    )


#------------------------------------------------------------------------------------------
# Presentation
#------------------------------------------------------------------------------------------

def print_law_table(samples: list[SampleLaw], repetitions: int) -> None:
    print()
    print(f"  Law of 1/√N   ({repetitions} repetitions per value of N)")
    print()
    print(
        f"  {'N':>10}  {'estimated value of π':>12}  {'true error':>11}"
        f"  {'theoretical error':>14}  {'error x √N':>16}"
    )
    print("  " + "-" * 72)

    for m in samples:
        print(
            f"  {m.n:>10,}  {m.estimate:>12.5f}  {m.error:>11.5f}"
            f"  {m.theoretical_error:>14.5f}  {m.error_for_sqr_n:>16.4f}"
        )

    constants = [m.error_for_sqr_n for m in samples]
    average = sum(constants) / len(constants)

    print(" " + "-" * 72)
    print()
    print(f"  The last column should stay close to {MEAN_ERROR_CONSTANT:.2f}")
    print(f"  Observed average: {average:.4f}")

    if len(samples) < 2:
        print()
        print(
            "  Note: With only a single value for N, no trend is apparent.\n"
            "  The 1/√N law is demonstrated only by comparing various values ​​of N.",
            file=sys.stderr,
        )
    else:
        print()
        print(f"  To reduce the error by half, N must be multiplied by 4.")
        print(f"  To gain one more decimal place, you must multiply N by 100.")
    print()


def print_convergence(
    points: list[int],
    estimates: list[float]
) -> None:
    print()
    print("  Convergence")
    print()
    print(f"  {'N':>12}  {'the estimated value of π':>13}  {'error':>10}")
    print(" " + "-" * 42)

    indexes = sorted({0, 1, 2, 4, 9, len(estimates) - 1})
    for i in indexes:
        if 0 <= i < len(estimates):
            n = points[i]
            error = abs(estimates[i] - REAL_PI)
            points_txt = f"{n:,}"
            if i == 0:
                points_txt = f"{n:,} (start)"

            print(f"  {points_txt:>12}  {estimates[i]:>13.5f} {error:>10.5f}")

    last = abs(estimates[-1] - REAL_PI)
    print()
    print(f"  Real value: {REAL_PI:.10f}")
    print(f"  Final error: {last:.5f}")
    print(f"  Error provided for by law: {theoretical_error(points[-1]):.5f}")
    print()


#------------------------------------------------------------------------------------------
# Persistence
#------------------------------------------------------------------------------------------

def save_json(route: Path, data: dict) -> None:
    route.parent.mkdir(parents=True, exist_ok=True)
    route.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Results saved at {route}")


#------------------------------------------------------------------------------------------
# Command-line interface
#------------------------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="montecarlo_pi.py",
        description="Estimation of pi using Monte Carlo.",
        epilog=(
            "Examples:\n"
            "python3 montecarlo_pi.py\n"
            "python3 montecarlo_pi.py --n 1000 10000 100000\n"
            "python3 montecarlo_pi.py --repetitions 500 --save\n"
            "python3 montecarlo_pi.py --convergence 1000000\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "-n", "--n",
        type=positive_integer,
        nargs="+",
        default=None,
        metavar="N",
        help=(
            "Values ​​of N for the 1/sqrt(N) rule table."
            "If not specified, the user is prompted (default: 100, 400, 1600, 6400, 25600, 102400)."
        )
    )

    parser.add_argument(
        "-r", "--repetitions",
        type=positive_integer,
        default=None,
        metavar="R",
        help=(
            "How many times to repeat each N in order to average out the error."
            "If it isn't written down, ask (def. 100)."
        )
    )

    parser.add_argument(
        "-c", "--convergence",
        type=positive_integer,
        default=None,
        metavar="N",
        help=(
            "Total points for the convergence curve"
            "If it’s not written down, ask (def. 100000)."
        )
    )

    parser.add_argument(
        "-b", "--batch",
        type=positive_integer,
        default=100,
        metavar="K",
        help="Minimum resolution of the convergence register (def. 100)."
    )

    parser.add_argument(
        "-s", "--seed",
        type=int,
        default=None,
        metavar="S",
        help="Random generator seed, for reproducible results."
    )

    parser.add_argument(
        "-s", "--save",
        action="store_true",
        default=None,
        help="Save the results in the 'results/' folder."
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow --convergence even if the memory limit is exceeded."
    )

    return parser

# Approximate memory required for the convergence curve per point:
#   2 float64 arrays (x, y) + 1 int64 accumulator + temporary values ​​≈ 32 bytes
BYTES_PER_POINT = 32
MEMORY_LIMIT_GB = 1.5

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # First, the values ​​are filled in, because the subsequent memory 
    # check needs to know how many points will be used.
    args = fill_missing(args)

    memory_gb = args.convergence * BYTES_PER_POINT / 1e9
    if memory_gb > MEMORY_LIMIT_GB and not args.force:
        maximum = int(MEMORY_LIMIT_GB * 1e9 / BYTES_PER_POINT)
        print()
        print(
            f"  --convergence {args.convergence:,} requires "
            f"{memory_gb:.1f} GB of memory,\n"
            f"and the safety limit is {MEMORY_LIMIT_GB} GB.",
            file=sys.stderr
        )
        print(
            f"  Use --convergence {maximum:,} or less, or add --force\n" 
            f"  if you really want to try.",
            file=sys.stderr
        )
        return 1

    rng = np.random.default_rng(args.seed)
    
    print()
    print("  Estimation of pi via Monte Carlo")
    print(f"  Seed: {args.seed if args.seed is not None else 'random'}")

    samples = law_table(args.n, args.repetitions, rng)
    print_law_table(samples, args.repetitions)

    points, estimates = convergence_curve(
        args.convergence, args.batch, rng
    )
    print_convergence(points, estimates)

    if args.save:
        save_json(
            Path("results") / "law_1sqrt_n.json",
            {
                "repetitions": args.repetitions,
                "seed": args.seed,
                "theoretical_constant": MEAN_ERROR_CONSTANT,
                "samples": [asdict(m) for m in samples]
            }
        )
        save_json(
            Path("results") / "convergence.json",
            {
                "points": points,
                "estimates": estimates,
                "real_pi": REAL_PI
            }
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
