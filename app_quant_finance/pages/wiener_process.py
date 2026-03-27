import inspect

import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="Wiener Process", page_icon="📊", layout="wide")
st.header("Wiener Process")

# --- Introduction ---
intro_col, formula_col = st.columns([3, 2])

with intro_col:
    st.write(
        "A **Wiener process**, also known as **Brownian motion**, is a continuous-time stochastic "
        "process that is widely used in finance to model random movements in asset prices."
    )
    st.write("A Wiener process $$W(t)$$ has the following key properties:")
    st.write("- $$W(0) = 0$$ — the process starts at zero")
    st.write(
        "- **Independent increments** — the movement between $$W(t)$$ and $$W(s)$$ is independent of the past"
    )
    st.write(
        "- **Normally distributed increments** — the increment $$W(t) - W(s)$$ has mean 0 and variance $$t - s$$"
    )
    st.write("- **Continuous paths** — the process has no jumps")

with formula_col:
    st.markdown("##### Increment Distribution")
    st.latex(r"W(t) - W(s) \sim N(0,\; t - s)")
    st.write("Where:")
    st.write("- $$W(t)$$ — value of the process at time $$t$$")
    st.write("- $$W(s)$$ — value of the process at time $$s$$")
    st.write("- $$N(0, t-s)$$ — normal distribution with mean 0 and variance $$t - s$$")

st.divider()

# --- Asset Pricing ---
st.markdown("##### Asset Pricing with a Wiener Process")

asset_formula_col, asset_desc_col = st.columns([2, 3])

with asset_formula_col:
    st.write("Asset prices can be modelled as a **stochastic process**:")
    st.latex(r"dS(t) = \mu S(t)\, dt + \sigma S(t)\, dW(t)")

with asset_desc_col:
    st.write("Where:")
    st.write("- $$S(t)$$ — asset price at time $$t$$")
    st.write("- $$dt$$ — infinitesimal time increment")
    st.write("- $$\\mu$$ — drift term representing the expected return")
    st.write("- $$\\sigma$$ — volatility of the log-returns (instantaneous volatility)")
    st.write("- $$dW(t)$$ — Wiener process increment (random shock)")

st.divider()

# --- Simulation functions ---


def simulate_paths(n_paths, n_steps, T, seed):
    np.random.seed(seed)
    dt = T / n_steps
    t = np.linspace(0, T, n_steps + 1)
    # Draw independent N(0, dt) increments
    dW = np.random.normal(0, np.sqrt(dt), (n_paths, n_steps))
    # Accumulate increments to form paths W(t)
    W = np.zeros((n_paths, n_steps + 1))
    W[:, 1:] = np.cumsum(dW, axis=1)
    return t, W


def compute_bounds(t):
    # Theoretical ±1σ and ±2σ envelopes: Std[W(t)] = √t
    std_bounds = np.sqrt(t)
    return std_bounds


def compute_convergence(W, T):
    final_values = W[:, -1]  # W(T) across all paths
    empirical_mean = np.mean(final_values)  # → 0
    empirical_std = np.std(final_values)  # → √T
    theoretical_std = np.sqrt(T)
    return final_values, empirical_mean, empirical_std, theoretical_std


# --- Interactive Simulation ---
st.markdown("#### Interactive Wiener Process Simulation")

st.write(
    "Simulate multiple Wiener process paths and observe the key statistical properties: "
    "$$W(0) = 0$$, $$E[W(t)] = 0$$, and $$\\text{Var}[W(t)] = t$$."
)

col1, col2 = st.columns(2)

with col1:
    n_paths = st.slider(
        "Number of Paths",
        min_value=1,
        max_value=200,
        value=50,
        help="The number of independent Wiener process paths to simulate. "
        "More paths gives a better approximation of the true distribution but is slower to compute. "
        "Try increasing this to see the sample mean and standard deviation converge to 0 and √T.",
    )
    n_steps = st.slider(
        "Number of Time Steps",
        min_value=50,
        max_value=1000,
        value=500,
        help="The number of discrete time steps used to approximate the continuous process. "
        "More steps produces smoother paths and a finer time grid, at the cost of more computation. "
        "The step size is dt = T / n_steps.",
    )

with col2:
    T = st.number_input(
        "Time Horizon (T)",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1,
        help="The total time over which the process is simulated, expressed in years. "
        "T = 1 represents one year, T = 0.5 represents six months. "
        "At time T, the distribution of W(T) is N(0, T), so a larger T produces wider, "
        "more dispersed paths. The theoretical standard deviation of W(T) is √T.",
    )
    seed = st.number_input(
        "Random Seed",
        min_value=0,
        value=42,
        step=1,
        help="Initialises the random number generator to ensure reproducibility. "
        "Two runs with the same seed and parameters will always produce identical paths. "
        "Change this value to generate a different set of random paths.",
    )

run = st.button("Run Simulation")

st.markdown("**Simulating the increments**")
code_col, info_col = st.columns(2)
with code_col:
    st.code(inspect.getsource(simulate_paths), language="python")
with info_col:
    st.info(
        "**What it does:** Generates `n_paths` independent realisations of a Wiener process over the interval [0, T].\n\n"
        "**How it works:** The time axis is divided into `n_steps` equally spaced intervals of width `dt = T / n_steps`. "
        "At each step, an increment `dW` is drawn from a normal distribution with mean 0 and standard "
        "deviation √dt — this directly encodes the property W(t) - W(s) ~ N(0, t - s). "
        "Paths are then built by cumulatively summing these increments using `np.cumsum`, "
        "so each row of W represents one complete sample path.\n\n"
        "**Why it matters:** Fixing the random seed ensures results are reproducible. Using matrix operations across "
        "all paths at once (rather than a Python loop) makes the simulation fast even for large path counts."
    )

st.markdown("**Computing theoretical bounds**")
code_col, info_col = st.columns(2)
with code_col:
    st.code(inspect.getsource(compute_bounds), language="python")
with info_col:
    st.info(
        "**What it does:** Computes the ±1σ and ±2σ envelopes that bound the spread of Wiener process paths over time.\n\n"
        "**How it works:** A key property of the Wiener process is that its variance grows linearly with time: "
        "Var[W(t)] = t, so Std[W(t)] = √t. The ±1σ envelope is simply √t, and ±2σ is 2√t. "
        "These are computed analytically — no simulation data is needed.\n\n"
        "**Why it matters:** Overlaying these bounds on the simulated paths provides a visual check that the simulation "
        "is correct. By the 68-95 rule, at any fixed time t approximately 68% of path values W(t) "
        "fall within ±√t, and 95% within ±2√t — this applies cross-sectionally at each point in time, "
        "not along individual paths, which can freely cross these boundaries. "
        "The widening envelope reflects that uncertainty grows over time — "
        "a fundamental feature of Brownian motion."
    )

st.markdown("**Checking convergence**")
code_col, info_col = st.columns(2)
with code_col:
    st.code(inspect.getsource(compute_convergence), language="python")
with info_col:
    st.info(
        "**What it does:** Verifies that the simulated paths exhibit the correct statistical properties at the terminal time T.\n\n"
        "**How it works:** The final column of W contains W(T) for each path — these are the terminal values of the process. "
        "The empirical mean and standard deviation of these values are computed and compared against "
        "the theoretical values: E[W(T)] = 0 and Std[W(T)] = √T.\n\n"
        "**Why it matters:** This is a sanity check grounded in the law of large numbers. With enough paths, the sample "
        "statistics must converge to the theoretical values. Increasing `n_paths` reduces the gap "
        "between empirical and theoretical, demonstrating that the simulation is statistically consistent "
        "with the Wiener process definition."
    )

if run:
    with st.spinner("Running simulation..."):
        t, W = simulate_paths(n_paths, n_steps, T, seed)
        std_bounds = compute_bounds(t)
        final_values, empirical_mean, empirical_std, theoretical_std = (
            compute_convergence(W, T)
        )

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Left plot: Sample Wiener process paths
        for i in range(n_paths):
            ax1.plot(t, W[i, :], alpha=0.3, linewidth=0.8)

        mean_path = np.mean(W, axis=0)
        ax1.plot(t, mean_path, color="red", linewidth=2, label="Mean Path")
        ax1.plot(
            t,
            std_bounds,
            color="black",
            linestyle="--",
            linewidth=1.5,
            label=r"$\pm 1\sigma$ ($\pm\sqrt{t}$)",
        )
        ax1.plot(t, -std_bounds, color="black", linestyle="--", linewidth=1.5)
        ax1.plot(
            t,
            2 * std_bounds,
            color="grey",
            linestyle="--",
            linewidth=1.5,
            label=r"$\pm 2\sigma$ ($\pm 2\sqrt{t}$)",
        )
        ax1.plot(t, -2 * std_bounds, color="grey", linestyle="--", linewidth=1.5)
        ax1.set_xlabel("Time")
        ax1.set_ylabel("W(t)")
        ax1.set_title(f"Wiener Process Paths ({n_paths} simulations)")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Right plot: Distribution of W(T)
        ax2.hist(
            final_values,
            bins=30,
            alpha=0.7,
            color="lightblue",
            edgecolor="black",
            density=True,
            label="Simulated W(T)",
        )
        x = np.linspace(final_values.min() - 0.5, final_values.max() + 0.5, 200)
        ax2.plot(
            x,
            norm.pdf(x, 0, np.sqrt(T)),
            color="red",
            linewidth=2,
            label=f"N(0, {T:.1f}) PDF",
        )
        ax2.axvline(
            empirical_mean,
            color="red",
            linestyle="-",
            linewidth=1.5,
            label=f"Mean: {empirical_mean:.4f}",
        )
        ax2.axvline(
            np.median(final_values),
            color="orange",
            linestyle="--",
            linewidth=1.5,
            label=f"Median: {np.median(final_values):.4f}",
        )
        ax2.set_xlabel("W(T)")
        ax2.set_ylabel("Probability Density")
        ax2.set_title(f"Distribution of W(T) at T={T:.1f}")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

    st.markdown('<div id="simulation-results"></div>', unsafe_allow_html=True)
    st.pyplot(fig)
    components.html(
        "<script>document.getElementById('simulation-results').scrollIntoView({behavior: 'smooth'});</script>",
        height=0,
    )

    # Summary metrics
    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Mean of W(T)",
        f"{empirical_mean:.4f}",
        help="The average terminal value W(T) across all simulated paths. "
        "By the definition of the Wiener process, E[W(t)] = 0 for all t. "
        "This should be close to zero — increase the number of paths to improve convergence.",
    )
    m2.metric(
        "Std Dev of W(T)",
        f"{empirical_std:.4f}",
        help="The empirical standard deviation of W(T) across all simulated paths. "
        "By the definition of the Wiener process, Var[W(t)] = t, so Std[W(T)] = √T. "
        "Compare this against the theoretical value to the right — they should be close.",
    )
    m3.metric(
        "Theoretical Std Dev (√T)",
        f"{theoretical_std:.4f}",
        help="The exact standard deviation predicted by theory: Std[W(T)] = √T. "
        "As the number of simulated paths increases, the empirical standard deviation "
        "to the left converges to this value by the law of large numbers.",
    )

    mean_close = abs(empirical_mean) < 0.5
    std_close = abs(empirical_std - theoretical_std) < 0.5
    w0_zero = all(W[:, 0] == 0)

    if w0_zero and mean_close and std_close:
        st.success(
            "**Wiener process properties confirmed:** "
            "W(0) = 0, E[W(t)] ≈ 0, Var[W(t)] ≈ t. "
            "Increase the number of paths for closer convergence to theoretical values."
        )
    else:
        st.info(
            "Try increasing the number of paths for the sample statistics "
            "to converge closer to the theoretical values."
        )

st.caption(
    "Wiener, N. (1923). 'Differential Space.' "
    "Journal of Mathematics and Physics, 2(1–4), 131–174."
)
