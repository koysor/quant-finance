import marimo

__generated_with = "0.17.7"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd

    return mo, np, pd, plt


@app.cell
def _(mo):
    mo.md(
        r"""
    ### Geometric Brownian Motion
    """
    )
    return


@app.cell
def _(mo):
    description = """The function simulate_gbm(S0, mu, sigma, T, dt, n_paths) simulates multiple paths of Geometric Brownian Motion (GBM), a common stochastic model used to represent asset prices.

    * Starts from an initial value $S_0$ (initial asset price).
    * Uses parameters:
      * $\mu$: the drift coefficient (expected return rate)
      * $\sigma$: the volatility (standard deviation of returns)
      * $T$: the total time horizon for the simulation
      * $dt$: the time step increment
      * $n_{paths}$: number of independent GBM paths to simulate.
    * Discretizes the time interval $[0, T]$ into steps of size $dt$
    * Generates random shocks from the standard normal distribution for each step and path
    * Iteratively builds paths according to the GBM formula 

    $S_t = S_{t-1} \\exp \\left( \\left( \\mu - \\frac{\\sigma^2}{2} \\right) dt + \\sigma \\sqrt{dt} Z_t \\right)$


    * Where $Z_t$ are independent standard normal variables
    * Returns the simulated time points and the matrix of simulated paths

    To summarise, this stimulates how an asset price evolves stochastically over time with drift and volatility, producing many sample paths useful for financial modelling and risk analysis.
    """
    mo.md(description).callout(kind="info")
    return


@app.cell
def _(mo, np):
    def simulate_gbm(S0, mu, sigma, T, dt, n_paths):
        """
        Simulate Geometric Brownian Motion paths

        Parameters:
        -----------
        S0 : float
            Initial value
        mu : float
            Drift coefficient (expected return)
        sigma : float
            Volatility coefficient
        T : float
            Total time
        dt : float
            Time step
        n_paths : int
            Number of paths to simulate

        Returns:
        --------
        t : array
            Time points
        paths : array
            Simulated paths (shape: n_steps x n_paths)
        """

        n_steps = int(T / dt)

        # Create an array of evenly spaced time points from 0 to T
        t = np.linspace(0, T, n_steps + 1)

        # Initialise paths array
        paths = np.zeros((n_steps + 1, n_paths))
        paths[0] = S0

        # Generate random shocks for all paths at once (vectorised)
        Z = np.random.standard_normal((n_steps, n_paths))

        # Simulate paths using the discrete GBM formula
        for i in range(1, n_steps + 1):
            paths[i] = paths[i - 1] * np.exp(
                (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z[i - 1]
            )

        return t, paths

    mo.show_code()
    return (simulate_gbm,)


@app.cell
def _(mo):
    mo.md(
        "The function np.random.standard_normal((n_steps, n_paths)) generates a NumPy array of shape (n_steps, n_paths) filled with random samples drawn from a standard normal distribution. A standard normal distribution is a normal (Gaussian) distribution with a mean of 0 and a standard deviation of 1, often visualized as a bell-shaped curve centered at zero."
    ).callout(kind="info")
    return


@app.cell
def _(np, simulate_gbm):
    # Set parameters
    S0 = 100  # Initial price
    mu = 0.1  # Annual drift (10% expected return)
    sigma = 0.2  # Annual volatility (20%)
    T = 1.0  # Time horizon (1 year)
    dt = 1 / 252  # Daily time steps (252 trading days per year)
    n_paths = 10_000  # Number of paths

    # Simulate paths
    np.random.seed(42)  # For reproducibility
    t, paths = simulate_gbm(S0, mu, sigma, T, dt, n_paths)
    return S0, T, dt, mu, n_paths, paths, sigma, t


@app.cell
def _(paths, pd):
    df_paths = pd.DataFrame(paths)
    return (df_paths,)


@app.cell
def _(df_paths):
    df_paths.head()
    return


@app.cell
def _(df_paths):
    df_paths.tail()
    return


@app.cell
def _(S0, T, dt, mo, mu, n_paths, sigma, simulate_gbm):
    mo.show_code(output=simulate_gbm(S0, mu, sigma, T, dt, n_paths), position="above")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    #### Plot
    """
    )
    return


@app.cell
def _(plt):
    # Plotting
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    return axes, fig


@app.cell
def _(axes, n_paths, paths, t):
    # Plot 1: All paths
    ax1 = axes[0, 0]
    ax1.plot(t, paths, alpha=0.2, linewidth=0.5)
    ax1.set_xlabel("Time (years)")
    ax1.set_ylabel("Price")
    ax1.set_title(f"All {n_paths} Geometric Brownian Motion Paths")
    ax1.grid(True, alpha=0.3)
    return


@app.cell
def _(S0, axes, mu, np, paths, t):
    # Plot 2: Sample of paths with mean
    ax2 = axes[0, 1]
    sample_paths = paths[:, :20]  # Plot only 20 paths for clarity
    ax2.plot(t, sample_paths, alpha=0.6, linewidth=1)
    mean_path = np.mean(paths, axis=1)
    ax2.plot(t, mean_path, "r-", linewidth=2, label="Mean path")
    ax2.plot(t, S0 * np.exp(mu * t), "g--", linewidth=2, label="Expected value")
    ax2.set_xlabel("Time (years)")
    ax2.set_ylabel("Price")
    ax2.set_title("Sample Paths with Mean")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    return


@app.cell
def _(T, axes, np, paths):
    # Plot 3: Distribution at final time
    ax3 = axes[1, 0]
    final_prices = paths[-1, :]

    ax3.hist(final_prices, bins=50, density=True, alpha=0.7, edgecolor="black")
    ax3.axvline(
        np.mean(final_prices),
        color="r",
        linestyle="--",
        label=f"Mean: {np.mean(final_prices):.2f}",
    )
    ax3.axvline(
        np.median(final_prices),
        color="g",
        linestyle="--",
        label=f"Median: {np.median(final_prices):.2f}",
    )
    ax3.set_xlabel("Final Price")
    ax3.set_ylabel("Density")
    ax3.set_title(f"Distribution of Final Prices at T={T}")
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    return (final_prices,)


@app.cell
def _(axes, np, paths, t):
    # Plot 4: Percentile bands
    ax4 = axes[1, 1]
    percentiles = [5, 25, 50, 75, 95]
    for p in percentiles:
        path_p = np.percentile(paths, p, axis=1)
        if p == 50:
            ax4.plot(t, path_p, "b-", linewidth=2, label=f"{p}th percentile (median)")
        else:
            ax4.plot(t, path_p, "--", alpha=0.7, label=f"{p}th percentile")

    ax4.fill_between(
        t,
        np.percentile(paths, 5, axis=1),
        np.percentile(paths, 95, axis=1),
        alpha=0.2,
        color="blue",
    )
    ax4.set_xlabel("Time (years)")
    ax4.set_ylabel("Price")
    ax4.set_title("Percentile Bands (5th to 95th)")
    ax4.legend(loc="upper left")
    ax4.grid(True, alpha=0.3)
    return


@app.cell
def _(S0, T, fig, mu, n_paths, plt, sigma):
    plt.suptitle(
        "Geometric Brownian Motion Simulation\n"
        + f"S₀={S0}, μ={mu}, σ={sigma}, T={T}, Paths={n_paths}",
        fontsize=14,
        fontweight="bold",
    )

    fig
    return


@app.cell
def _(mo):
    mo.md(
        r"""
    #### Statistics
    """
    )
    return


@app.cell
def _(S0, T, final_prices, mo, mu, np):
    with mo.redirect_stdout():
        print("Simulation Statistics:")
        print("-" * 40)
        print(f"Initial value: {S0:.2f}")
        print(f"Mean final value: {np.mean(final_prices):.2f}")
        print(f"Median final value: {np.median(final_prices):.2f}")
        print(f"Std dev of final values: {np.std(final_prices):.2f}")
        print(f"Expected final value (theory): {S0 * np.exp(mu * T):.2f}")
        print(f"5th percentile: {np.percentile(final_prices, 5):.2f}")
        print(f"95th percentile: {np.percentile(final_prices, 95):.2f}")
        print(f"Probability of ending below S0: {np.mean(final_prices < S0):.2%}")
        print(f"Probability of ending above S0: {np.mean(final_prices > S0):.2%}")
    return


if __name__ == "__main__":
    app.run()
