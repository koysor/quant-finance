import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import sympy as sp
    from scipy.stats import lognorm, norm

    return lognorm, mo, norm, np, pd, plt, sp


@app.cell
def _(mo):
    mo.md(r"""
    # Asset Returns: From Random Walk to Geometric Brownian Motion

    Almost every model in quantitative finance, from Black–Scholes to Monte Carlo
    value-at-risk, starts from one assumption about how asset prices move:

    $$dS = \mu S\,dt + \sigma S\,dX.$$

    This notebook builds that stochastic differential equation (SDE) from the ground up.
    It starts with a simple, discrete model of **returns** as a random walk, lets the
    time step shrink to zero to arrive at the SDE, and then solves the SDE exactly
    with Itô's lemma.  Along the way the simulations are compared with theory.

    You will see:

    1. why we model **returns** rather than prices, and why the random part scales with $\sqrt{\Delta t}$;
    2. how the random walk becomes the SDE in the limit $\Delta t \to 0$;
    3. a symbolic Itô's lemma derivation of the exact solution;
    4. interactive simulations comparing the discrete random walk with the exact solution,
       the distribution of returns and of the final price, and how the two models converge.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 1. Returns, not prices

    Let $S_i$ be the asset price at time $t_i = i\,\Delta t$.  The **return** over the
    $i$-th step is the relative change in price

    $$R_i = \frac{S_{i+1} - S_i}{S_i}.$$

    Returns are the natural quantity to model because they do not depend on the price
    level: a £1 move means a lot for a £10 share and very little for a £1,000 share,
    whereas a 1% return means the same for both.  Empirically, returns over short
    periods look roughly like independent draws from a distribution with a small mean
    and a much larger spread.

    ## 2. Returns as a random walk

    The simplest model of that behaviour is

    $$R_i = \mu\,\Delta t + \sigma Z_i \sqrt{\Delta t}, \qquad Z_i \sim N(0, 1) \text{ independent},$$

    so that the price evolves as

    $$S_{i+1} = S_i \left(1 + \mu\,\Delta t + \sigma Z_i \sqrt{\Delta t}\right).$$

    | Symbol | Meaning |
    |---|---|
    | $S_i$ | asset price after $i$ steps, starting from $S_0$ |
    | $\Delta t$ | length of one time step, in years |
    | $T$ | time horizon in years, so there are $T / \Delta t$ steps |
    | $\mu$ | drift: the expected annual growth rate of the price |
    | $\sigma$ | volatility: the annualised standard deviation of returns |
    | $Z_i$ | independent standard normal draws |

    Each return has mean $\mathbb{E}[R_i] = \mu\,\Delta t$ and standard deviation
    $\sigma\sqrt{\Delta t}$.

    **Why $\sqrt{\Delta t}$?**  Independent returns add up, and so do their variances.
    Over a year made of $1/\Delta t$ steps the variance of the total return is
    $\frac{1}{\Delta t}\,\sigma^2 \Delta t = \sigma^2$, whatever the step size.  Any other
    power of $\Delta t$ would make the yearly variance either explode or vanish as the
    step shrinks.  The drift, in contrast, scales with $\Delta t$ itself, so over short
    steps the noise term $\sigma\sqrt{\Delta t}$ is far larger than the drift $\mu\,\Delta t$.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 3. From the random walk to the SDE

    Write the change in price over one step as $\delta S = S_{i+1} - S_i$:

    $$\delta S = \mu S\,\delta t + \sigma S\,Z\sqrt{\delta t}.$$

    The term $Z\sqrt{\delta t}$ is a normal random variable with mean $0$ and variance
    $\delta t$: it is the increment of a Brownian motion over the step.  Letting the
    step shrink to an infinitesimal $dt$ and writing that increment as $dX$ gives the
    **stochastic differential equation for geometric Brownian motion (GBM)**:

    $$dS = \mu S\,dt + \sigma S\,dX, \qquad dX \sim N(0, dt).$$

    Here $dX$ is the Brownian increment (written $dW_t$ elsewhere in this repo), with

    $$\mathbb{E}[dX] = 0, \qquad \mathbb{E}[dX^2] = dt.$$

    The second property is what makes stochastic calculus different from ordinary
    calculus: $dX^2$ is of order $dt$, not $dt^2$, so it cannot be ignored when we
    expand a function of $S$ to first order in $dt$.  In the limit we can treat
    $dX^2 = dt$.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 4. Solving the SDE with Itô's lemma

    To solve the SDE, look at $\log S$.  A Taylor expansion to second order gives

    $$d(\log S) = \frac{1}{S}\,dS - \frac{1}{2S^2}\,dS^2.$$

    Substitute $dS = \mu S\,dt + \sigma S\,dX$, replace $dX^2$ by $dt$ and drop every
    term smaller than order $dt$ (that is $dt^2$ and $dt\,dX$, of order $dt^{3/2}$).
    The cell below does exactly that with `sympy`.
    """)
    return


@app.cell
def _(mo, sp):
    _S, _mu, _sigma, _dt, _dX = sp.symbols("S mu sigma dt dX", positive=True)
    _dS = _mu * _S * _dt + _sigma * _S * _dX

    # Second-order Taylor expansion of log(S): f'(S) dS + 1/2 f''(S) dS^2
    _f = sp.log(_S)
    _expansion = sp.diff(_f, _S) * _dS + sp.Rational(1, 2) * sp.diff(_f, _S, 2) * _dS**2

    # Itô's rule dX^2 = dt, then keep terms up to order dt (dt counts 1, dX counts 1/2)
    _expanded = sp.expand(_expansion).xreplace({_dX**2: _dt})
    _poly = sp.Poly(_expanded, _dt, _dX)
    expr_dlogS = sum(
        _coeff * _dt**_a * _dX**_b
        for (_a, _b), _coeff in _poly.terms()
        if _a + sp.Rational(_b, 2) <= 1
    )
    expr_dlogS = sp.collect(sp.expand(expr_dlogS), [_dt, _dX])

    mo.show_code(
        mo.md(
            rf"""
            Full expansion before dropping terms:

            $$d(\log S) = {sp.latex(_expanded)}$$

            Keeping terms up to order $dt$:

            $$d(\log S) = {sp.latex(expr_dlogS)}$$
            """
        )
    )
    return (expr_dlogS,)


@app.cell
def _(mo):
    mo.md(r"""
    So $\log S$ is a Brownian motion with constant drift $\mu - \tfrac{1}{2}\sigma^2$:

    $$d(\log S) = \left(\mu - \tfrac{1}{2}\sigma^2\right) dt + \sigma\,dX.$$

    Integrating from $0$ to $T$, with $X_T \sim N(0, T)$ the total Brownian increment,

    $$S_T = S_0 \exp\!\left(\left(\mu - \tfrac{1}{2}\sigma^2\right) T + \sigma X_T\right).$$

    So $\log S_T$ is normal and $S_T$ is **lognormal**, with

    $$\mathbb{E}[S_T] = S_0 e^{\mu T}, \qquad
    \operatorname{Var}[S_T] = S_0^2 e^{2\mu T}\left(e^{\sigma^2 T} - 1\right), \qquad
    \operatorname{median}(S_T) = S_0 e^{(\mu - \frac{1}{2}\sigma^2) T}.$$

    Because the exact solution holds over any interval, we can simulate it step by step
    with no discretisation error:

    $$S_{i+1} = S_i \exp\!\left(\left(\mu - \tfrac{1}{2}\sigma^2\right)\Delta t + \sigma Z_i\sqrt{\Delta t}\right).$$
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 5. Implementation

    Both simulations below take the **same** array of standard normal shocks $Z_i$, so
    each random-walk path can be compared directly with the exact GBM path driven by
    the same randomness.
    """)
    return


@app.cell
def _(mo, np):
    def simulate_random_walk(S0, mu, sigma, T, n_steps, shocks):
        """
        Simulate prices whose returns follow a discrete random walk.

        Each step applies R_i = mu * dt + sigma * Z_i * sqrt(dt), so
        S_{i+1} = S_i * (1 + R_i).

        Parameters
        ----------
        S0 : float
            Initial price.
        mu : float
            Annual drift.
        sigma : float
            Annual volatility.
        T : float
            Time horizon in years.
        n_steps : int
            Number of time steps.
        shocks : numpy.ndarray
            Standard normal draws, shape (n_steps, n_paths).

        Returns
        -------
        paths : numpy.ndarray
            Prices, shape (n_steps + 1, n_paths), with paths[0] = S0.
        returns : numpy.ndarray
            One-step returns R_i, shape (n_steps, n_paths).
        """
        dt = T / n_steps
        returns = mu * dt + sigma * np.sqrt(dt) * shocks
        growth = np.cumprod(1.0 + returns, axis=0)
        paths = S0 * np.vstack([np.ones(shocks.shape[1]), growth])
        return paths, returns

    def simulate_gbm_exact(S0, mu, sigma, T, n_steps, shocks):
        """
        Simulate geometric Brownian motion from its exact solution.

        Each step applies
        S_{i+1} = S_i * exp((mu - sigma^2 / 2) * dt + sigma * Z_i * sqrt(dt)),
        which has no discretisation error.

        Parameters
        ----------
        S0 : float
            Initial price.
        mu : float
            Annual drift.
        sigma : float
            Annual volatility.
        T : float
            Time horizon in years.
        n_steps : int
            Number of time steps.
        shocks : numpy.ndarray
            Standard normal draws, shape (n_steps, n_paths).

        Returns
        -------
        numpy.ndarray
            Prices, shape (n_steps + 1, n_paths), with the first row equal to S0.
        """
        dt = T / n_steps
        log_steps = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * shocks
        log_paths = np.vstack([np.zeros(shocks.shape[1]), np.cumsum(log_steps, axis=0)])
        return S0 * np.exp(log_paths)

    mo.show_code()
    return simulate_gbm_exact, simulate_random_walk


@app.cell
def _(mo):
    mo.md(r"""
    ## 6. Interactive simulation

    Change the parameters to see how the random walk and the exact solution behave.
    Try a **large step** (annual) with **high volatility** to see the random walk break
    down, and a **daily** step to see the two models agree.
    """)
    return


@app.cell
def _(mo):
    s0_slider = mo.ui.slider(
        start=50, stop=200, step=5, value=100, label="Initial price $S_0$"
    )
    mu_slider = mo.ui.slider(
        start=-0.2, stop=0.4, step=0.01, value=0.08, label="Drift $\\mu$"
    )
    sigma_slider = mo.ui.slider(
        start=0.05, stop=0.8, step=0.01, value=0.2, label="Volatility $\\sigma$"
    )
    years_slider = mo.ui.slider(
        start=1, stop=5, step=1, value=1, label="Horizon $T$ (years)"
    )
    steps_dropdown = mo.ui.dropdown(
        options={
            "Annual (1 per year)": 1,
            "Quarterly (4 per year)": 4,
            "Monthly (12 per year)": 12,
            "Weekly (52 per year)": 52,
            "Daily (252 per year)": 252,
        },
        value="Monthly (12 per year)",
        label="Time step $\\Delta t$",
    )
    paths_dropdown = mo.ui.dropdown(
        options={"100": 100, "500": 500, "1,000": 1_000, "2,000": 2_000},
        value="1,000",
        label="Number of paths",
    )
    seed_input = mo.ui.number(
        start=0, stop=10_000, step=1, value=42, label="Random seed"
    )

    mo.hstack(
        [
            mo.vstack([s0_slider, mu_slider, sigma_slider]),
            mo.vstack([years_slider, steps_dropdown, paths_dropdown, seed_input]),
        ],
        justify="start",
        gap=4,
    )
    return (
        mu_slider,
        paths_dropdown,
        s0_slider,
        seed_input,
        sigma_slider,
        steps_dropdown,
        years_slider,
    )


@app.cell
def _(
    mu_slider,
    np,
    paths_dropdown,
    s0_slider,
    seed_input,
    sigma_slider,
    simulate_gbm_exact,
    simulate_random_walk,
    steps_dropdown,
    years_slider,
):
    S0 = float(s0_slider.value)
    mu = mu_slider.value
    sigma = sigma_slider.value
    T = float(years_slider.value)
    steps_per_year = steps_dropdown.value
    n_paths = paths_dropdown.value

    n_steps = int(T * steps_per_year)
    dt_step = T / n_steps
    time_grid = np.linspace(0.0, T, n_steps + 1)

    _rng = np.random.default_rng(int(seed_input.value))
    shocks = _rng.standard_normal((n_steps, n_paths))

    paths_rw, returns_rw = simulate_random_walk(S0, mu, sigma, T, n_steps, shocks)
    paths_exact = simulate_gbm_exact(S0, mu, sigma, T, n_steps, shocks)
    return (
        S0,
        T,
        dt_step,
        mu,
        n_paths,
        n_steps,
        paths_exact,
        paths_rw,
        returns_rw,
        sigma,
        time_grid,
    )


@app.cell
def _(S0, mu, np, paths_exact, paths_rw, plt, time_grid):
    _n_show = min(20, paths_rw.shape[1])
    fig_paths, _ax = plt.subplots(figsize=(11, 5))
    for _j in range(_n_show):
        _colour = f"C{_j % 10}"
        _ax.plot(time_grid, paths_exact[:, _j], color=_colour, linewidth=1, alpha=0.8)
        _ax.plot(
            time_grid,
            paths_rw[:, _j],
            color=_colour,
            linewidth=1,
            linestyle="--",
            alpha=0.8,
        )
    _ax.plot(
        time_grid,
        S0 * np.exp(mu * time_grid),
        color="black",
        linewidth=2.5,
        label=r"$\mathbb{E}[S_t] = S_0 e^{\mu t}$",
    )
    _ax.axhline(0.0, color="grey", linewidth=0.8)
    _ax.plot([], [], color="grey", linewidth=1, label="Exact GBM (solid)")
    _ax.plot(
        [], [], color="grey", linewidth=1, linestyle="--", label="Random walk (dashed)"
    )
    _ax.set_xlabel("Time (years)")
    _ax.set_ylabel("Price")
    _ax.set_title(
        f"{_n_show} paths: random walk (dashed) and exact GBM (solid) with the same shocks"
    )
    _ax.legend(loc="upper left")
    _ax.grid(True, alpha=0.3)
    fig_paths.tight_layout()
    fig_paths
    return


@app.cell
def _(dt_step, mo, mu, n_paths, paths_rw, sigma):
    _n_non_positive = int((paths_rw <= 0).any(axis=0).sum())
    _drift = mu * dt_step
    _noise = sigma * dt_step**0.5
    mo.md(
        f"""
        **Drift against noise.**  With this time step the expected return per step is
        μΔt = {_drift:.5f}, while its standard deviation is σ√Δt = {_noise:.5f},
        about {abs(_noise / _drift) if _drift != 0 else float("inf"):,.1f} times larger.
        Over short steps the randomness dominates; the drift only shows up over many steps.

        **Can prices go negative?**  {_n_non_positive} of {n_paths:,} random-walk paths
        reached zero or below.  A random-walk step multiplies the price by
        1 + μΔt + σZ√Δt, which is negative when Z is very negative, and that is likely
        when σ√Δt is large.  The exact GBM multiplies by an exponential, so it always
        stays positive.
        """
    ).callout(kind="info")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Distribution of one-step returns

    By construction each return $R_i$ is normal with mean $\mu\,\Delta t$ and standard
    deviation $\sigma\sqrt{\Delta t}$.  The histogram of all simulated returns should sit
    on that curve.
    """)
    return


@app.cell
def _(dt_step, mu, norm, np, plt, returns_rw, sigma):
    _returns = returns_rw.ravel()
    _grid = np.linspace(_returns.min(), _returns.max(), 400)
    fig_returns, _ax = plt.subplots(figsize=(11, 4.5))
    _ax.hist(
        _returns,
        bins=80,
        density=True,
        alpha=0.6,
        edgecolor="black",
        label="Simulated $R_i$",
    )
    _ax.plot(
        _grid,
        norm.pdf(_grid, loc=mu * dt_step, scale=sigma * np.sqrt(dt_step)),
        color="C3",
        linewidth=2,
        label=r"$N(\mu\Delta t,\ \sigma^2\Delta t)$",
    )
    _ax.set_xlabel("One-step return $R_i$")
    _ax.set_ylabel("Density")
    _ax.set_title(f"One-step returns over Δt = {dt_step:.4f} years")
    _ax.legend()
    _ax.grid(True, alpha=0.3)
    fig_returns.tight_layout()
    fig_returns
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Distribution of the final price

    Under GBM, $S_T$ is lognormal: $\log S_T \sim N\!\left(\log S_0 + (\mu - \tfrac{1}{2}\sigma^2)T,\ \sigma^2 T\right)$.
    The distribution is skewed to the right, so its **median** sits below its **mean**.
    """)
    return


@app.cell
def _(S0, T, lognorm, mu, np, paths_exact, paths_rw, plt, sigma):
    _final_exact = paths_exact[-1]
    _final_rw = paths_rw[-1]
    _dist = lognorm(s=sigma * np.sqrt(T), scale=S0 * np.exp((mu - 0.5 * sigma**2) * T))
    _mean = S0 * np.exp(mu * T)
    _median = S0 * np.exp((mu - 0.5 * sigma**2) * T)

    _upper = np.percentile(np.concatenate([_final_exact, _final_rw]), 99.5)
    _lower = min(0.0, _final_rw.min())
    _bins = np.linspace(_lower, _upper, 70)
    _grid = np.linspace(max(_lower, 1e-6), _upper, 400)

    fig_terminal, _ax = plt.subplots(figsize=(11, 4.5))
    _ax.hist(_final_exact, bins=_bins, density=True, alpha=0.5, label="Exact GBM $S_T$")
    _ax.hist(
        _final_rw,
        bins=_bins,
        density=True,
        histtype="step",
        linewidth=1.5,
        color="black",
        label="Random walk $S_T$",
    )
    _ax.plot(
        _grid, _dist.pdf(_grid), color="C3", linewidth=2, label="Lognormal density"
    )
    _ax.axvline(
        _mean, color="C2", linestyle="--", label=f"Mean $S_0e^{{\\mu T}}$ = {_mean:.2f}"
    )
    _ax.axvline(
        _median,
        color="C1",
        linestyle=":",
        linewidth=2,
        label=f"Median $S_0e^{{(\\mu-\\sigma^2/2)T}}$ = {_median:.2f}",
    )
    _ax.set_xlabel("Final price $S_T$")
    _ax.set_ylabel("Density")
    _ax.set_title(f"Distribution of the final price at T = {T:g} years")
    _ax.legend()
    _ax.grid(True, alpha=0.3)
    fig_terminal.tight_layout()
    fig_terminal
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Simulation against theory
    """)
    return


@app.cell
def _(
    S0,
    T,
    dt_step,
    mo,
    mu,
    n_paths,
    n_steps,
    norm,
    np,
    paths_exact,
    paths_rw,
    pd,
    returns_rw,
    sigma,
):
    _final_exact = paths_exact[-1]
    _final_rw = paths_rw[-1]
    _exact_returns = paths_exact[1:] / paths_exact[:-1] - 1.0

    _theory_mean = S0 * np.exp(mu * T)
    _theory_std = _theory_mean * np.sqrt(np.exp(sigma**2 * T) - 1.0)
    _theory_median = S0 * np.exp((mu - 0.5 * sigma**2) * T)
    _theory_below = norm.cdf(-(mu - 0.5 * sigma**2) * np.sqrt(T) / sigma)

    stats_table = pd.DataFrame(
        {
            "Random walk": [
                returns_rw.mean(),
                returns_rw.std(),
                _final_rw.mean(),
                _final_rw.std(),
                np.median(_final_rw),
                np.mean(_final_rw < S0),
            ],
            "Exact GBM": [
                _exact_returns.mean(),
                _exact_returns.std(),
                _final_exact.mean(),
                _final_exact.std(),
                np.median(_final_exact),
                np.mean(_final_exact < S0),
            ],
            "Theory": [
                mu * dt_step,
                sigma * np.sqrt(dt_step),
                _theory_mean,
                _theory_std,
                _theory_median,
                _theory_below,
            ],
        },
        index=[
            "Mean one-step return",
            "Std of one-step return",
            "Mean of S_T",
            "Std of S_T",
            "Median of S_T",
            "P(S_T < S_0)",
        ],
    ).round(5)

    mo.vstack(
        [
            mo.md(
                f"{n_paths:,} paths of {n_steps:,} steps.  The theory column is exact for the "
                "one-step returns of the random walk and for the final price under GBM."
            ),
            stats_table,
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 7. The random walk converges to GBM

    The random walk is the Euler–Maruyama discretisation of the SDE, so it should
    approach the exact solution as the step shrinks.  For each step size below, both
    models are driven by the same Brownian path: the fine daily shocks are summed to
    give the shocks for coarser steps.  The average gap
    $\mathbb{E}\,\lvert S_T^{\text{RW}} - S_T^{\text{exact}}\rvert$ shrinks roughly in
    proportion to $\sqrt{\Delta t}$, the strong order of convergence of Euler–Maruyama.
    """)
    return


@app.cell
def _(S0, T, mu, np, sigma, simulate_gbm_exact, simulate_random_walk):
    _n_conv_paths = 2_000
    _fine_per_year = 252
    _n_fine = int(T * _fine_per_year)
    _rng = np.random.default_rng(2024)
    _fine_shocks = _rng.standard_normal((_n_fine, _n_conv_paths))

    convergence_rows = []
    for _per_year in [1, 2, 4, 12, 63, 252]:
        _block = _fine_per_year // _per_year
        _n_coarse = _n_fine // _block
        # Sum blocks of fine shocks and rescale, so every step size sees the same path
        _coarse = _fine_shocks.reshape(_n_coarse, _block, _n_conv_paths).sum(axis=1)
        _coarse = _coarse / np.sqrt(_block)
        _rw, _ = simulate_random_walk(S0, mu, sigma, T, _n_coarse, _coarse)
        _ex = simulate_gbm_exact(S0, mu, sigma, T, _n_coarse, _coarse)
        convergence_rows.append((T / _n_coarse, np.mean(np.abs(_rw[-1] - _ex[-1]))))
    return (convergence_rows,)


@app.cell
def _(convergence_rows, np, plt):
    _dts = np.array([_row[0] for _row in convergence_rows])
    _errors = np.array([_row[1] for _row in convergence_rows])
    fig_convergence, _ax = plt.subplots(figsize=(11, 4.5))
    _ax.loglog(_dts, _errors, "o-", linewidth=2, label="Mean absolute gap at $T$")
    _ax.loglog(
        _dts,
        _errors[-1] * np.sqrt(_dts / _dts[-1]),
        "k--",
        label=r"Reference slope $\propto \sqrt{\Delta t}$",
    )
    _ax.set_xlabel("Time step Δt (years)")
    _ax.set_ylabel(r"$\mathbb{E}\,|S_T^{RW} - S_T^{exact}|$")
    _ax.set_title("Random walk against exact GBM as the step shrinks (2,000 paths)")
    _ax.legend()
    _ax.grid(True, which="both", alpha=0.3)
    fig_convergence.tight_layout()
    fig_convergence
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Summary

    - Modelling **returns** as $R_i = \mu\,\Delta t + \sigma Z_i\sqrt{\Delta t}$ gives a
      random walk in which the drift scales with $\Delta t$ and the noise with
      $\sqrt{\Delta t}$, so the variance over a year does not depend on the step size.
    - Letting $\Delta t \to 0$ turns the random walk into the SDE
      $dS = \mu S\,dt + \sigma S\,dX$, with $\mathbb{E}[dX] = 0$ and $\mathbb{E}[dX^2] = dt$.
    - Itô's lemma, the Taylor expansion with $dX^2 = dt$, gives
      $d(\log S) = (\mu - \tfrac{1}{2}\sigma^2)\,dt + \sigma\,dX$, so $S_T$ is lognormal
      and always positive.
    - The mean of $S_T$ grows at rate $\mu$, but its median only at
      $\mu - \tfrac{1}{2}\sigma^2$: volatility drags the typical outcome below the average.
    - With small steps the random walk and the exact solution agree closely; with large
      steps and high volatility the random walk can produce negative prices.
    """).callout(kind="info")
    return


if __name__ == "__main__":
    app.run()
