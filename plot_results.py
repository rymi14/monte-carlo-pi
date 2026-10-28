
"""
Generate the project's graphs from the saved results.
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import numpy as np
except ModuleNotFoundError:
    print("matplotlib is missing. Install it with:")
    print("    pip install -r requirements.txt")
    print("Or, if you are using a virtual environment:")
    print("    source .venv/bin/activate && pip install -r requirements.txt")
    raise SystemExit(1) from None

DATA_FOLDER = Path("results")   # JSON is regenerated; it is included in .gitignore.
IMG_FOLDER = Path("img")        # PNG files are versioned for the README

# Constants are imported to avoid repeating the formula in two files.
from montecarlo_pi import DEVIATION_CONSTANT, REAL_PI # noqa: E402


def plot_convergence() -> bool:
    path = DATA_FOLDER / "convergence.json"
    if not path.exists():
        print(f"{path} not found. Run this first:")
        print("    python montecarlo_pi.py --save")
        return False

    data = json.loads(path.read_text(encoding="utf-8"))
    points = np.array(data["points"])
    estimates = np.array(data["estimates"])

    # π comes from the imported constant, not from the JSON; the file includes "pi_real" 
    # solely as a reference for anyone who might open it manually.
    real_pi = REAL_PI

    # Predicted error band: pi ± deviation. It narrows as 1/√N.
    deviation = DEVIATION_CONSTANT / np.sqrt(points) 

    # The zoom panel only makes sense if there are enough points.
    with_zoom = len(points) >= 30
    rows = 2 if with_zoom else 1
    fig, axes = plt.subplot(rows, 1, figsize=(10, 4.5 * rows))
    if rows == 1:
        axes = [axes]

    def decorate(ax, title, with_stripe):
        ax.plot(points, estimates, linewidth=0.9, color="#1f77b4", label="Estimate")

        if with_stripe:
            ax.fill_between(
                points, real_pi - deviation, real_pi + deviation,
                color="crimson", alpha=0.15,
                label="Predicted margin of error (±1 standard deviation)"
            )
        
        ax.axhline(
            real_pi, color="crimson", linestyle="--",
            linewidth=1.5, label=f"Real π ={real_pi:.6f}"
        )
        ax.set_xlabel("Number of points generated (N)")
        ax.set_ylabel("Estimation of π")
        ax.set_title(title)
        ax.set_xscale("log")
        ax.grid(alpha=0.3)
        ax.legend(loc="upper right", fontsize=9)

    decorate(
        axes[0],
        "Convergence of the estimate of π",
        with_stripe=True
    )

    if with_zoom:
        # The final 25% of the data points, where it appears to have stabilized.
        court = int(len(points) * 0.75)
        ax = axes[1]
        decorate(ax, "Detail: the final 25% of the run", with_stripe=True)
        ax.set_xlim(left=points[court], right=points[-1])

        # The vertical axis covers both the error range and the data, ensuring 
        # that the curve is never cut off.
        data_scope = np.max(np.abs(estimates[court] - real_pi)) * 1.3
        edge = max(float(deviation[court]), data_scope) * 1.2
        ax.set_ylim(real_pi - edge, real_pi + edge)

    fig.tight_layout()
    destination = IMG_FOLDER / "convergence.png"
    fig.savefig(destination, dpi=150)
    plt.close(fig)
    print(f"   Saved {destination}")
    return True

def plot_law() -> bool:
    path = DATA_FOLDER / "law_1sqrt_n.json"
    if not path.exists():
        print(f"{path} not found. Run this first:")
        print("    python montecarlo_pi.py --save")
        return False

    data = json.loads(path.read_text(encoding="utf-8"))
    samples = data["samples"]

    n = np.array([m["n"] for m in samples])
    real_error = np.array([m["error"] for m in samples])
    theoretical_error = np.array([m["theoretical_error"] for m in samples])

    fig, ax = plt.subplots(figsize=(10, 6))

    # With only one point, there is no slope to adjust: a straight line requires 
    # at least two points. In that case, the graph provides no useful information.
    various_n = len(n) >= 2

    style = "o-" if various_n else "o"
    ax.loglog(
        n, 
        theoretical_error, 
        "--", 
        color="crimson", 
        linewidth=2, 
        label="Theoretical: C / √N"
    )
    ax.loglog(
        n,
        real_error,
        style, 
        color="#1f77b4",
        linewidth=2,
        label="Measured actual error"
    )

    if various_n:
        pending = np.polyfit(np.log(n), np.log(real_error), 1)[0]
        ax.set_title(
            "The 1/√N law\n"
            f"slope of the line on a log-log scale = {pending:.3f} "
            f"(theoretical: -0.5)"
        )
    else:
        ax.set_title(
            "The 1/√N law\n"
            "There is only one value for N; use several N values ​​to see the trend."
        )
    ax.set_xlabel("Number of points (N)")
    ax.set_ylabel("Mean absolute error")
    ax.grid(alpha=0.3, which="both")
    ax.legend()

    fig.tight_layout()
    destination = IMG_FOLDER / "law_1sqrt_n.png"
    fig.savefig(destination, dpi=150)
    plt.close(fig)
    print(f"   Saved {destination}")
    return True

def main() -> int:
    if not DATA_FOLDER.exists():
        print("The 'results/' folder does not exist.")
        print("First, run: python montecarlo_pi.py --guardar")
        return 1
    
    IMG_FOLDER.mkdir(exist_ok=True)

    plot_law()
    plot_convergence()
    print()
    print("   The charts are located in 'img/' and are version-controlled for the README.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
