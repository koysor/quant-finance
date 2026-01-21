import marimo

__generated_with = "0.18.0"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt

    return mo, np, plt


@app.cell
def _(mo):
    mean_slider = mo.ui.slider(start=-10, stop=10, step=0.1, value=0, label="Mean")
    mean_slider
    return (mean_slider,)


@app.cell
def _(mo):
    std_dev_slider = mo.ui.slider(
        start=0, stop=5, step=0.1, value=0.5, label="Standard Deviation"
    )
    std_dev_slider
    return (std_dev_slider,)


@app.cell
def _(mo):
    bins_slider = mo.ui.slider(start=1, stop=100, step=1, value=30, label="Bins")
    bins_slider
    return (bins_slider,)


@app.cell
def _(bins_slider, mean_slider, std_dev_slider):
    mean = mean_slider.value
    standard_deviation = std_dev_slider.value
    bins = bins_slider.value
    return bins, mean, standard_deviation


@app.cell
def _(mo):
    mo.md(
        r"""
    ### Normal Distribution

    The Normal Distribution is symmetric and bell-shaped.  It is described by two parameters: the mean (μ) and the standard deviation (σ).

    The np.random.normal function returns random numbers following a bell-shaped curve centered at loc with variability controlled by scale.
    """
    )
    return


@app.cell
def _(mean, np, standard_deviation):
    normal_data = np.random.normal(loc=mean, scale=standard_deviation, size=1_000)
    return (normal_data,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ### Lognormal Distribution

    The function np.random.lognormal(mean=0.0, sigma=1.0, size=None) draws samples from a log-normal distribution.
    The parameter mean (μ) represents the mean of the underlying normal distribution's logarithm. It is not the mean of the log-normal distribution itself, but rather the mean of the normally distributed logarithm of the random variable.
    Sigma is the standard deviation (σ) of the underlying normal distribution's logarithm. It controls the spread of the log-normal distribution.
    """
    )
    return


@app.cell
def _(mean, np, standard_deviation):
    lognormal_data = np.random.lognormal(
        mean=mean, sigma=standard_deviation, size=1_000
    )
    return (lognormal_data,)


@app.cell
def _(mo):
    mo.md(
        r"""
    ### Plot Normal vs Lognormal
    """
    )
    return


@app.cell
def _(bins, lognormal_data, normal_data, plt):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

    ax1.hist(normal_data, bins=bins, color="skyblue", edgecolor="black")
    ax1.set(title="Normal Distribution", xlabel="Value", ylabel="Frequency")

    ax2.hist(lognormal_data, bins=bins, color="lightgreen", edgecolor="black")
    ax2.set(title="Lognormal Distribution", xlabel="Value", ylabel="Frequency")

    plt.tight_layout()

    # Return the figure as the last expression to display it
    fig
    return


if __name__ == "__main__":
    app.run()
