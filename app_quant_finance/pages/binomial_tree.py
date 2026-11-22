import math

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import streamlit as st
from scipy.stats import norm

from quant_finance.pricing.binomial import (
    BinomialLattice,
    Payoff,
    binomial_lattice,
    binomial_price,
    binomial_price_closed_form,
    digital_call_payoff,
    terminal_distribution,
)
from quant_finance.pricing.black_scholes import black_scholes_price

st.set_page_config(page_title="The Binomial Tree", page_icon="📊", layout="wide")
st.header("The Binomial Tree")

st.write(
    "Over one time step the stock can only go up or down.  That is enough to build a portfolio of the "
    "option and the stock with no risk at all, and no-arbitrage then fixes the option price: the "
    "real-world probability of an up move never appears.  This page builds the tree from the stock's "
    "SDE, prices an option on it by backward induction, shows the replicating portfolio at every node, "
    "and follows the price to the Black–Scholes limit.  The one-step worked example with zero interest "
    "is on the **Binomial Model** page of the Options app."
)


# ---------------------------------------------------------------------------
# Inputs shared by every tab
# ---------------------------------------------------------------------------

PAYOFFS = {
    "Call": "$\\max(S_T - K, 0)$",
    "Put": "$\\max(K - S_T, 0)$",
    "Digital call": "$1$ if $S_T > K$, $\\tfrac12$ if $S_T = K$, else $0$",
    "Power call": "$\\max(S_T^2 - K^2, 0)$",
}

col1, col2, col3, col4 = st.columns(4)
with col1:
    S0 = st.number_input("Stock price $S$", min_value=1.0, value=100.0, step=1.0)
    K = st.number_input("Strike $K$", min_value=1.0, value=100.0, step=1.0)
with col2:
    T = st.slider("Time to expiry $T$ (years)", 0.1, 3.0, 1.0, 0.1)
    sigma = st.slider("Volatility $\\sigma$ (%)", 5, 80, 20) / 100
with col3:
    r = st.slider("Risk-free rate $r$ (%)", 0.0, 30.0, 5.0, 0.25) / 100
    q = st.slider("Dividend yield $q$ (%)", 0.0, 10.0, 0.0, 0.25) / 100
with col4:
    payoff_name = st.selectbox("Payoff", list(PAYOFFS), index=1)
    american = st.toggle("American (early exercise)", value=True)
    N = st.slider("Number of steps $N$", 1, 8, 4)

st.caption(f"Payoff at expiry: {PAYOFFS[payoff_name]}")


def make_payoff(name: str, strike: float) -> Payoff:
    """The payoff function for one of the names in PAYOFFS."""
    if name == "Call":
        return lambda s: np.maximum(s - strike, 0.0)
    if name == "Put":
        return lambda s: np.maximum(strike - s, 0.0)
    if name == "Digital call":
        return digital_call_payoff(strike)
    return lambda s: np.maximum(s**2 - strike**2, 0.0)


payoff = make_payoff(payoff_name, K)
dt = T / N
u = math.exp(sigma * math.sqrt(dt))
d = 1 / u
growth = math.exp((r - q) * dt)
arbitrage_free = d < growth < u

lattice: BinomialLattice | None = None
european: BinomialLattice | None = None
if arbitrage_free:
    lattice = binomial_lattice(
        S0, K, T, r, sigma, N, american=american, q=q, payoff=payoff
    )
    european = binomial_lattice(
        S0, K, T, r, sigma, N, american=False, q=q, payoff=payoff
    )


def need_lattice() -> bool:
    """Warn and return False when the inputs give an arbitrage tree."""
    if lattice is None:
        st.error(
            "With these inputs $e^{(r-q)\\Delta t}$ lies outside $(d, u)$, so the tree admits an "
            "arbitrage and cannot price anything.  See the **u, d and p** tab, then use more steps, "
            "a lower rate or a higher volatility."
        )
        return False
    return True


def draw_lattice(lat: BinomialLattice, reveal_from: int, title: str) -> None:
    """Draw the tree with the stock price and option value at each node.

    Values are shown only from step `reveal_from` to expiry, so the reader can
    follow the induction backwards; nodes where an American option is
    exercised early are coloured orange.
    """
    n = len(lat.stock) - 1
    fig, ax = plt.subplots(figsize=(min(2.5 + 1.7 * n, 15), max(3.5, 1.0 * n + 2)))
    for i in range(n):
        for j in range(i + 1):
            y = i - 2 * j
            ax.plot([i, i + 1], [y, y + 1], color="#B0BEC5", linewidth=1, zorder=1)
            ax.plot([i, i + 1], [y, y - 1], color="#B0BEC5", linewidth=1, zorder=1)
    for i in range(n + 1):
        for j in range(i + 1):
            y = i - 2 * j
            revealed = i >= reveal_from
            if not revealed:
                face, text = "#ECEFF1", f"S={lat.stock[i][j]:.2f}\nV=?"
            elif lat.exercise[i][j]:
                face, text = (
                    "#FFCC80",
                    f"S={lat.stock[i][j]:.2f}\nV={lat.value[i][j]:.3f}\nexercise",
                )
            else:
                face, text = (
                    "#BBDEFB",
                    f"S={lat.stock[i][j]:.2f}\nV={lat.value[i][j]:.3f}",
                )
            ax.text(
                i,
                y,
                text,
                ha="center",
                va="center",
                fontsize=7,
                zorder=2,
                bbox=dict(
                    boxstyle="round,pad=0.3", facecolor=face, edgecolor="#607D8B"
                ),
            )
    ax.set_xlim(-0.6, n + 0.6)
    ax.set_ylim(-n - 1, n + 1)
    ax.set_xticks(range(n + 1))
    ax.set_xlabel("Time step $i$")
    ax.set_yticks([])
    for side in ("left", "right", "top"):
        ax.spines[side].set_visible(False)
    ax.set_title(title)
    st.pyplot(fig)
    plt.close(fig)


tabs = st.tabs(
    [
        "Tree structure",
        "u, d and p",
        "Backward induction",
        "Replication at a node",
        "Real-world vs risk-neutral",
        "Continuous-time limit",
    ]
)

# ---------------------------------------------------------------------------
# 1. Tree structure
# ---------------------------------------------------------------------------

with tabs[0]:
    st.subheader("A recombining tree")

    def binomial_tree(n: int, p: float) -> nx.DiGraph:
        """
        Generates a NetworkX binomial tree.

        Each node represents a state (level, successes) and each edge a
        transition with its probability: p for a success, 1 - p for a failure.
        The tree recombines (a success then a failure reaches the same node as a
        failure then a success), so level k has k + 1 nodes and the tree has
        (n + 1)(n + 2) / 2 nodes in all. It is built one level at a time, so each
        node is expanded once.

        Parameters:
        n (int): Number of trials.
        p (float): Probability of success.

        Returns:
        G (networkx.DiGraph): Directed graph representing the binomial tree.
        """
        G = nx.DiGraph()
        G.add_node((0, 0))  # (level, successes)

        for level in range(n):
            for successes in range(level + 1):
                node = (level, successes)
                G.add_edge(node, (level + 1, successes + 1), probability=p)
                G.add_edge(node, (level + 1, successes), probability=1 - p)

        return G

    def display_binomial_tree(n: int, p: float) -> None:
        """Draw the tree, labelling each node with the number of paths into it."""
        G = binomial_tree(n, p)
        pos = {(level, ups): (level, ups - level / 2) for level, ups in G.nodes()}
        labels = {
            (level, ups): f"({level},{ups})\n{math.comb(level, ups)}"
            for level, ups in G.nodes()
        }
        edge_labels = {
            k: f"{v:.2f}" for k, v in nx.get_edge_attributes(G, "probability").items()
        }

        fig, ax = plt.subplots()
        nx.draw(
            G,
            pos,
            labels=labels,
            node_size=900,
            node_color="lightblue",
            font_size=7,
            ax=ax,
        )
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=edge_labels, font_size=7, label_pos=0.3, ax=ax
        )
        ax.set_title(f"Binomial tree (n={n}, p={p})")
        st.pyplot(fig)
        plt.close(fig)

    left, right = st.columns([1, 2])
    with left:
        n_structure = st.slider("Number of steps", min_value=1, max_value=6, value=3)
        p_structure = st.slider(
            "Probability of an up move",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
        )
        st.info(
            "Each node is labelled $(i, j)$ with the number of paths that reach it below:\n"
            "- $i$ = time step, $j$ = number of up moves\n"
            "- an up then a down move reach the same node as a down then an up, so the tree "
            "**recombines**: step $i$ has $i + 1$ nodes, and expiry has $N + 1$\n"
            "- $\\binom{i}{j}$ paths reach node $(i, j)$, so its probability is "
            "$\\binom{i}{j} p^j (1 - p)^{i - j}$: the number of up moves is $\\mathrm{Bin}(i, p)$"
        )
        terminal = pd.DataFrame(
            {
                "Up moves j": range(n_structure + 1),
                "Paths": [math.comb(n_structure, j) for j in range(n_structure + 1)],
                "Probability": [
                    math.comb(n_structure, j)
                    * p_structure**j
                    * (1 - p_structure) ** (n_structure - j)
                    for j in range(n_structure + 1)
                ],
            }
        )
        st.dataframe(
            terminal,
            hide_index=True,
            column_config={"Probability": st.column_config.NumberColumn(format="%.4f")},
        )
        st.caption(
            f"{2**n_structure} paths but only {n_structure + 1} terminal nodes: a non-recombining tree "
            "would need a node per path."
        )
    with right:
        display_binomial_tree(n_structure, p_structure)

# ---------------------------------------------------------------------------
# 2. From the SDE to u, d and p
# ---------------------------------------------------------------------------

with tabs[1]:
    st.subheader("Choosing $u$, $d$ and $p$ from the continuous model")
    st.write(
        "The stock follows $dS = \\mu S\\,dt + \\sigma S\\,dW_t$.  Split $[0, T]$ into $N$ steps of "
        "length $\\Delta t = T/N$ and let the stock move from $S$ to $uS$ or $dS$ at each step.  The "
        "Cox–Ross–Rubinstein (CRR) choice matches the mean and variance of the log return to first "
        "order in $\\Delta t$ and makes the tree recombine with $ud = 1$:"
    )
    st.latex(
        r"u = e^{\sigma\sqrt{\Delta t}}, \qquad d = \frac{1}{u}, \qquad "
        r"p = \frac{e^{(r - q)\Delta t} - d}{u - d}"
    )
    st.caption(
        "Some texts write $v$ for the down factor $d$ and $q$ for the risk-neutral probability $p$."
    )

    st.latex(
        rf"\Delta t = {dt:.4f}, \quad u = {u:.5f}, \quad d = {d:.5f}, \quad "
        rf"e^{{(r - q)\Delta t}} = {growth:.5f}"
    )

    if arbitrage_free:
        p_rn = (growth - d) / (u - d)
        st.success(
            f"No-arbitrage holds: $d = {d:.5f} < e^{{(r-q)\\Delta t}} = {growth:.5f} < u = {u:.5f}$, "
            f"so $p = {p_rn:.5f}$ lies in $(0, 1)$."
        )
        mean_log = (2 * p_rn - 1) * sigma * math.sqrt(dt)
        var_log = 4 * p_rn * (1 - p_rn) * sigma**2 * dt
        moments = pd.DataFrame(
            {
                "Quantity over one step": [
                    "E[S(t+Δt)/S(t)]",
                    "E[ln(S(t+Δt)/S(t))]",
                    "Var[ln(S(t+Δt)/S(t))]",
                ],
                "Tree (under p)": [p_rn * u + (1 - p_rn) * d, mean_log, var_log],
                "Continuous model (under ℚ)": [
                    growth,
                    (r - q - 0.5 * sigma**2) * dt,
                    sigma**2 * dt,
                ],
            }
        )
        st.dataframe(
            moments,
            hide_index=True,
            column_config={
                c: st.column_config.NumberColumn(format="%.6f")
                for c in ("Tree (under p)", "Continuous model (under ℚ)")
            },
        )
        st.write(
            "The expected growth matches **exactly**: that is how $p$ is defined.  The log-return mean "
            "and variance match only to first order in $\\Delta t$, so the match improves as $N$ grows.  "
            "Try $N = 1$ and $N = 8$."
        )
    else:
        if growth >= u:
            trade = (
                "the bank account does at least as well as the stock even in the up state, and "
                "strictly better in the down state.  Short the stock (paying its dividends) and lend "
                "the proceeds: at the end of the step the loan repays at least what it costs to buy the "
                "stock back, and more if it fell, so there is no loss and a chance of a gain"
            )
        else:
            trade = (
                "the stock does at least as well as the bank account even in the down state, and "
                "strictly better in the up state.  Borrow to buy the stock: at the end of the step it is "
                "worth at least the loan, and more if it rose, so there is no loss and a chance of a gain"
            )
        st.error(
            f"No-arbitrage fails: $d = {d:.5f}$, $e^{{(r-q)\\Delta t}} = {growth:.5f}$, $u = {u:.5f}$.  "
            f"Here {trade}.  Then $p = {(growth - d) / (u - d):.4f}$ is not a probability, and the tree "
            "cannot price options.  A large $\\Delta t$ with a high rate causes this: add steps."
        )

    st.info(
        "Why $p$ makes the stock grow at the risk-free rate: if it grew faster or slower in expectation "
        "under the pricing probability, the discounted stock would not be fairly priced against the bank "
        "account.  $p$ is a **pricing device**, chosen to make that true, not a forecast of how likely an "
        "up move is."
    )

# ---------------------------------------------------------------------------
# 3. Backward induction
# ---------------------------------------------------------------------------

with tabs[2]:
    st.subheader("Pricing on a multi-step tree by backward induction")
    st.write(
        "At expiry each node is worth its payoff.  Working back one step at a time, each node is worth "
        "the discounted risk-neutral expectation of its two successors.  For an American option, the "
        "holder can also exercise, so the node takes the larger of the two."
    )
    st.latex(
        r"V_{i,j} = e^{-r\Delta t}\big[p\,V_{i+1,j} + (1 - p)\,V_{i+1,j+1}\big]"
        r"\qquad\text{(European)}"
    )
    st.latex(
        r"V_{i,j} = \max\Big(e^{-r\Delta t}\big[p\,V_{i+1,j} + (1 - p)\,V_{i+1,j+1}\big],\ "
        r"\text{Payoff}(S_{i,j})\Big)\qquad\text{(American)}"
    )
    st.caption(
        "Here node $(i, j)$ is at step $i$ after $j$ down moves, so $(i+1, j)$ is its up successor."
    )

    if need_lattice():
        assert lattice is not None and european is not None
        reveal_from = st.slider(
            "Show values from step … to expiry (slide left to run the induction back to today)",
            min_value=0,
            max_value=N,
            value=0,
        )
        style = "American" if american else "European"
        draw_lattice(lattice, reveal_from, f"{style} {payoff_name.lower()}, N = {N}")

        exercise_nodes = [
            (i, j)
            for i, level in enumerate(lattice.exercise)
            for j in np.flatnonzero(level)
        ]
        c1, c2, c3 = st.columns(3)
        c1.metric(f"{style} price V₀", f"{lattice.value[0][0]:.4f}")
        c2.metric("European price", f"{european.value[0][0]:.4f}")
        c3.metric(
            "Early-exercise premium",
            f"{lattice.value[0][0] - european.value[0][0]:.4f}",
        )
        if american:
            if exercise_nodes:
                st.success(
                    f"Early exercise is optimal at {len(exercise_nodes)} node(s), coloured orange: "
                    + ", ".join(f"$({i}, {j})$" for i, j in exercise_nodes)
                    + ".  There the payoff from exercising now beats the discounted value of waiting."
                )
            else:
                st.info(
                    "No node exercises early, so the American and European prices agree.  Without "
                    "dividends an American call is never exercised early; try a deep in-the-money put."
                )
        st.warning(
            "Pitfall: for an American option each step must be discounted and checked against exercise.  "
            "Discounting once at the end gives the European price, because the exercise check needs a "
            "value at every node."
        )

# ---------------------------------------------------------------------------
# 4. Replication at a node
# ---------------------------------------------------------------------------

with tabs[3]:
    st.subheader("The hedge ratio and the riskless portfolio")
    st.write(
        "Hold one option and short $\\Delta$ shares: $\\Pi = V - \\Delta S$.  Choose $\\Delta$ so that "
        "$\\Pi$ is worth the same in both states at the next step.  Then $\\Pi$ is riskless, so to avoid "
        "arbitrage it must earn exactly the risk-free rate."
    )
    st.latex(
        r"V^+ - \Delta\,uS = V^- - \Delta\,dS \quad\Longrightarrow\quad "
        r"\Delta = \frac{V^+ - V^-}{(u - d)S}"
    )
    st.write(
        "With a dividend yield $q$ the short position must also pay the dividends, so it owes "
        "$e^{q\\Delta t}\\Delta$ shares by the end of the step.  Equating the two states then gives "
        "$\\Delta = e^{-q\\Delta t}(V^+ - V^-)/\\big((u - d)S\\big)$, which is the formula above when "
        "$q = 0$."
    )

    if need_lattice():
        assert lattice is not None
        nodes = [(i, j) for i in range(N) for j in range(i + 1)]
        i, j = st.selectbox(
            "Node $(i, j)$: step $i$, after $j$ down moves",
            nodes,
            format_func=lambda node: (
                f"({node[0]}, {node[1]}), S = {lattice.stock[node[0]][node[1]]:.2f}"
            ),
        )
        S_node = lattice.stock[i][j]
        S_up, S_down = lattice.stock[i + 1][j], lattice.stock[i + 1][j + 1]
        V_up, V_down = lattice.value[i + 1][j], lattice.value[i + 1][j + 1]
        delta = lattice.delta[i][j]
        pi_now = lattice.bond[i][j]
        owed = delta * math.exp(q * dt)  # shares owed at the end, with dividends
        pi_up, pi_down = V_up - owed * S_up, V_down - owed * S_down
        discount = math.exp(-r * dt)
        risk_neutral = discount * (lattice.p * V_up + (1 - lattice.p) * V_down)

        left, right = st.columns(2)
        with left:
            st.latex(
                rf"""
                \begin{{aligned}}
                S &= {S_node:.4f}, & uS &= {S_up:.4f}, & dS &= {S_down:.4f} \\
                & & V^+ &= {V_up:.4f}, & V^- &= {V_down:.4f} \\[4pt]
                \Delta &= e^{{-q\Delta t}}\,
                    \frac{{{V_up:.4f} - {V_down:.4f}}}{{{S_up:.4f} - {S_down:.4f}}} = {delta:.4f}
                \end{{aligned}}
                """
            )
            st.latex(
                rf"""
                \begin{{aligned}}
                \text{{Up:}}\quad V^+ - e^{{q\Delta t}}\Delta\,uS &= {pi_up:.4f} \\
                \text{{Down:}}\quad V^- - e^{{q\Delta t}}\Delta\,dS &= {pi_down:.4f}
                \end{{aligned}}
                """
            )
            st.caption(
                "The two are equal: the portfolio carries no risk over this step."
            )
        with right:
            st.latex(
                rf"""
                \begin{{aligned}}
                \Pi &= e^{{-r\Delta t}} \times {pi_up:.4f} = {pi_now:.4f} \\
                V &= \Pi + \Delta S = {pi_now:.4f} + {delta:.4f} \times {S_node:.4f}
                   = {pi_now + delta * S_node:.4f} \\[4pt]
                V &= e^{{-r\Delta t}}\big[p V^+ + (1 - p) V^-\big] = {risk_neutral:.4f}
                \end{{aligned}}
                """
            )
            st.caption(
                f"With p = {lattice.p:.4f}.  Replication and risk-neutral expectation give the same "
                "value: the second is the first, rearranged."
            )
            if lattice.exercise[i][j]:
                st.warning(
                    f"This node exercises early, so its value is the payoff {lattice.value[i][j]:.4f}, "
                    f"not the {risk_neutral:.4f} it costs to replicate waiting."
                )
        st.info(
            "The replicating portfolio holds $\\Delta$ shares, reinvesting their dividends, and "
            "$V - \\Delta S$ in cash; a negative "
            "amount means borrowing.  Its cost is the option's price, and nothing in the calculation used "
            "the real-world probability of an up move.  $\\Delta$ changes from node to node, so the hedge "
            "is rebalanced at every step."
        )

# ---------------------------------------------------------------------------
# 5. Real-world vs risk-neutral
# ---------------------------------------------------------------------------

with tabs[4]:
    st.subheader("The real-world drift drops out")
    st.write(
        "Suppose the stock drifts at $\\mu$ under the real-world measure $\\mathbb{P}$.  Then the "
        "real-world probability of an up move is"
    )
    st.latex(r"p^{\mathbb{P}} = \frac{e^{\mu\Delta t} - d}{u - d}.")
    st.write(
        "The tree price does not use $p^{\\mathbb{P}}$ at all.  The tempting alternative, the real-world "
        "expected payoff discounted at $r$, does depend on $\\mu$, and is wrong whenever "
        "$\\mu \\ne r - q$."
    )

    if need_lattice():
        assert european is not None
        mu = st.slider("Real-world drift $\\mu$ (%)", -20.0, 40.0, 12.0, 1.0) / 100

        def naive_price(drift: float) -> float:
            """e^{-rT} E^P[payoff], or NaN when p^P is not a probability."""
            try:
                prices, probabilities = terminal_distribution(S0, T, drift, sigma, N)
            except ValueError:
                return float("nan")
            return math.exp(-r * T) * float(np.sum(probabilities * payoff(prices)))

        p_real = (math.exp(mu * dt) - d) / (u - d)
        tree_value = european.value[0][0]
        naive = naive_price(mu)
        c1, c2, c3 = st.columns(3)
        c1.metric("Real-world probability pᴾ", f"{p_real:.4f}")
        c2.metric("Risk-neutral probability p", f"{european.p:.4f}")
        c3.metric("Tree price (European)", f"{tree_value:.4f}")
        if 0 < p_real < 1:
            st.write(
                f"Real-world expected payoff discounted at $r$: **{naive:.4f}**, "
                f"{'above' if naive > tree_value else 'below'} the tree price by "
                f"{abs(naive - tree_value):.4f}."
            )
        else:
            st.warning(
                "With this drift and step size $p^{\\mathbb{P}}$ is not a probability; use more steps."
            )

        drifts = np.linspace(-0.2, 0.4, 61)
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(
            drifts * 100,
            [naive_price(m) for m in drifts],
            label="$e^{-rT}\\,\\mathbb{E}^{\\mathbb{P}}$[payoff]",
        )
        ax.axhline(
            tree_value, color="black", linestyle="--", label="Tree price (replication)"
        )
        ax.axvline(
            (r - q) * 100,
            color="grey",
            linewidth=0.8,
            linestyle=":",
            label="$\\mu = r - q$",
        )
        ax.scatter([mu * 100], [naive], color="#EF5350", zorder=3)
        ax.set_xlabel("Real-world drift $\\mu$ (%)")
        ax.set_ylabel("Price")
        ax.set_title(f"{payoff_name} on a {N}-step tree: price against the drift")
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close(fig)
        st.info(
            "The two lines meet only where $\\mu = r - q$, when $\\mathbb{P}$ and $\\mathbb{Q}$ agree.  "
            "The option is replicated by stock and cash, so its price is the cost of replication, which "
            "depends only on $u$, $d$ and $r$.  Investors who disagree about $\\mu$, or about risk, must "
            "still agree on the price."
        )

# ---------------------------------------------------------------------------
# 6. Closed form and continuous-time limit
# ---------------------------------------------------------------------------

with tabs[5]:
    st.subheader("The price as one sum")
    st.write(
        "The number of up moves to expiry is $\\mathrm{Bin}(N, p)$ under the risk-neutral measure, so "
        "for a European option the backward induction collapses to one discounted expectation:"
    )
    st.latex(
        r"V_0 = e^{-rT}\sum_{k=0}^{N}\binom{N}{k} p^k (1 - p)^{N-k}\,"
        r"\text{Payoff}\big(S u^k d^{N-k}\big)"
    )

    if need_lattice():
        assert european is not None
        prices, probabilities = terminal_distribution(S0, T, r, sigma, N, q)
        payoffs = payoff(prices)
        table = pd.DataFrame(
            {
                "Up moves k": range(N + 1),
                "Paths C(N, k)": [math.comb(N, k) for k in range(N + 1)],
                "S_T": prices,
                "Probability": probabilities,
                "Payoff": payoffs,
                "Probability × payoff": probabilities * payoffs,
            }
        )
        st.dataframe(
            table,
            hide_index=True,
            column_config={
                c: st.column_config.NumberColumn(format="%.4f")
                for c in ("S_T", "Probability", "Payoff", "Probability × payoff")
            },
        )
        closed = binomial_price_closed_form(S0, K, T, r, sigma, N, q=q, payoff=payoff)
        st.write(
            f"$e^{{-rT}} \\times {float(np.sum(probabilities * payoffs)):.4f} = {closed:.4f}$, the same "
            f"as backward induction for the European option ({european.value[0][0]:.4f})."
        )

    st.subheader("The continuous-time limit")
    st.write(
        "$\\ln S_T$ is $\\ln S$ plus a sum of $N$ independent $\\pm\\sigma\\sqrt{\\Delta t}$ steps.  By "
        "the central limit theorem it becomes Normal as $N \\to \\infty$, with the Black–Scholes mean "
        "$\\ln S + (r - q - \\tfrac{1}{2}\\sigma^2)T$ and variance $\\sigma^2 T$, so $S_T$ becomes "
        "lognormal and the tree price converges to the Black–Scholes price."
    )
    n_limit = st.slider("Number of steps for the limit", 2, 500, 50)
    try:
        big_prices, big_probabilities = terminal_distribution(
            S0, T, r, sigma, n_limit, q
        )
    except ValueError:
        st.error(
            "This many steps still admits an arbitrage with these inputs; add steps."
        )
    else:
        log_prices = np.log(big_prices)
        spacing = 2 * sigma * math.sqrt(T / n_limit)
        mean = math.log(S0) + (r - q - 0.5 * sigma**2) * T
        grid = np.linspace(
            mean - 4 * sigma * math.sqrt(T), mean + 4 * sigma * math.sqrt(T), 400
        )
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.bar(
            log_prices,
            big_probabilities / spacing,
            width=spacing * 0.8,
            color="#90CAF9",
            label=f"Tree, N = {n_limit} (probability / node spacing)",
        )
        ax.plot(
            grid,
            norm.pdf(grid, mean, sigma * math.sqrt(T)),
            color="black",
            label="Normal density",
        )
        ax.set_xlim(grid[0], grid[-1])
        ax.set_xlabel("$\\ln S_T$")
        ax.set_ylabel("Density")
        ax.set_title("Distribution of the log price at expiry")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close(fig)

    # Power calls have no Black–Scholes formula here, so they fall back to a call
    kind = {"Put": "put", "Digital call": "digital call"}.get(payoff_name, "call")
    st.write(
        f"Error against Black–Scholes for a European {kind} as the number of steps grows, on log "
        "scales so that an error proportional to $1/N$ is a straight line.  Odd and even $N$ are in "
        "different colours.  The price against $N$ is plotted on the Options app's **Binomial Model** "
        "page."
    )

    @st.cache_data
    def convergence_errors(
        S: float, K: float, T: float, r: float, sigma: float, q: float, kind: str
    ) -> tuple[float, np.ndarray]:
        """Black–Scholes price and |tree − Black–Scholes| for N = 1, ..., 200."""
        if kind == "digital call":
            d2 = (math.log(S / K) + (r - q - 0.5 * sigma**2) * T) / (
                sigma * math.sqrt(T)
            )
            exact = math.exp(-r * T) * float(norm.cdf(d2))
        else:
            exact = float(black_scholes_price(S, K, T, r, sigma, q, kind))
        errors = []
        for n in range(1, 201):
            try:
                if kind == "digital call":
                    price = binomial_price_closed_form(
                        S, K, T, r, sigma, n, q=q, payoff=digital_call_payoff(K)
                    )
                else:
                    price = binomial_price(S, K, T, r, sigma, n, kind, q=q)
            except ValueError:
                price = float("nan")
            errors.append(abs(price - exact))
        return exact, np.array(errors)

    bs, errors_arr = convergence_errors(S0, K, T, r, sigma, q, kind)
    steps = np.arange(1, 201)
    fig, ax = plt.subplots(figsize=(9, 4))
    odd = steps % 2 == 1
    ax.plot(
        steps[odd], errors_arr[odd], "o", markersize=3, label="Odd N", color="#2196F3"
    )
    ax.plot(
        steps[~odd],
        errors_arr[~odd],
        "o",
        markersize=3,
        label="Even N",
        color="#EF5350",
    )
    # Reference line C / N through the typical size of N × error over the larger N
    scaled = steps[100:] * errors_arr[100:]
    scaled = scaled[np.isfinite(scaled) & (scaled > 0)]
    if scaled.size:
        level = float(np.median(scaled))
        ax.plot(
            steps, level / steps, color="grey", linestyle="--", label="$\\propto 1/N$"
        )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Number of steps N")
    ax.set_ylabel("|tree − Black–Scholes|")
    ax.set_title(f"Convergence of the European {kind} (Black–Scholes {bs:.4f})")
    ax.legend()
    ax.grid(True, alpha=0.3, which="both")
    st.pyplot(fig)
    plt.close(fig)
    st.warning(
        "Pitfall: convergence is not smooth.  The error shrinks roughly like $1/N$, but it oscillates "
        "between odd and even $N$ and with where the strike falls between the terminal nodes.  Move "
        "$K$ away from $S$ to see it."
    )
    if payoff_name == "Digital call":

        def strict_digital(s: np.ndarray) -> np.ndarray:
            return (s > K).astype(float)

        strict_errors = []
        for n in (50, 200):
            try:
                strict = binomial_price_closed_form(
                    S0, K, T, r, sigma, n, q=q, payoff=strict_digital
                )
                strict_errors.append(f"{abs(strict - bs):.4f} at $N = {n}$")
            except ValueError:
                strict_errors.append(f"undefined at $N = {n}$")
        st.info(
            "A digital's payoff jumps at $K$, so a node on the strike needs a convention.  With "
            "$S = K$ and even $N$ the middle node lands exactly on $K$; this page pays $\\tfrac12$ "
            "there.  Paying $0$ on the strike would give an error of "
            + " and ".join(strict_errors)
            + " with these inputs; when $S = K$ that error shrinks only like $1/\\sqrt{N}$."
        )

# ---------------------------------------------------------------------------
# Complete markets and check yourself
# ---------------------------------------------------------------------------

with st.expander("Complete markets: why two states, and not three"):
    st.write(
        "With two states and two traded assets (stock and cash), any payoff can be replicated: two "
        "equations, two unknowns.  Add a third state and the same two assets give three equations in "
        "two unknowns, which in general have no solution.  Example: one step, zero interest, $S = 100$, "
        "and a call struck at 100."
    )
    states = np.array([110.0, 100.0, 90.0])
    call_payoff = np.maximum(states - 100.0, 0.0)
    design = np.column_stack([states, np.ones(3)])
    (delta_ls, cash_ls), *_ = np.linalg.lstsq(design, call_payoff, rcond=None)
    hedge_ls = design @ np.array([delta_ls, cash_ls])
    delta_bin = (call_payoff[0] - call_payoff[2]) / (states[0] - states[2])
    cash_bin = call_payoff[2] - delta_bin * states[2]
    completeness = pd.DataFrame(
        {
            "State": ["Up", "Middle", "Down"],
            "S": states,
            "Call payoff": call_payoff,
            "Best two-asset hedge (least squares)": hedge_ls,
            "Hedge error": hedge_ls - call_payoff,
        }
    )
    st.dataframe(completeness, hide_index=True)
    # Risk-neutral probabilities (q_u, 1 - 2 q_u, q_u) price the stock fairly for any q_u in (0, 1/2)
    st.write(
        f"No portfolio of stock and cash replicates the call in all three states (the best has "
        f"$\\Delta = {delta_ls:.3f}$ and still misses by up to {np.abs(hedge_ls - call_payoff).max():.3f}).  "
        f"Every set of probabilities $(q, 1 - 2q, q)$ with $0 < q < \\tfrac12$ prices the stock at 100, "
        f"and each gives a different call price $10q$, so no-arbitrage only bounds the price in "
        f"$(0, {10 * 0.5:.0f})$.  Drop the middle state and the hedge $\\Delta = {delta_bin:.2f}$, cash "
        f"${cash_bin:.0f}$ is exact, giving the unique price {delta_bin * 100 + cash_bin:.0f}."
    )

with st.expander("Check yourself"):
    st.markdown(
        "1. **Derive $\\Delta$ for one step** from the condition that the hedged portfolio is riskless.  \n"
        "   *Answer:* set $V^+ - \\Delta uS = V^- - \\Delta dS$; see the **Replication at a node** tab, "
        "which does it with the numbers at any node."
    )
    st.markdown(
        "2. **Why does the real probability of an up move not affect the price?**  \n"
        "   *Answer:* the option is replicated by stock and cash, whose cost uses only $u$, $d$ and $r$.  "
        "The **Real-world vs risk-neutral** tab shows the price stays flat as $\\mu$ moves."
    )
    st.markdown(
        "3. **What arbitrage exists if $e^{r\\Delta t} > u$?**  \n"
        "   *Answer:* short the stock and lend the proceeds; the loan repays more than the stock costs to "
        "buy back, even after an up move.  Set $N = 1$ and a high $r$ in the **u, d and p** tab."
    )
    try:
        two_step = binomial_lattice(S0, K, T, r, sigma, 2, "put", american=True, q=q)
    except ValueError:
        answer4 = (
            "a two-step tree admits an arbitrage with these inputs; lower $r$ or raise "
            "$\\sigma$ to see the answer"
        )
    else:
        early = [
            (i, j)
            for i, level in enumerate(two_step.exercise)
            for j in np.flatnonzero(level)
        ]
        where = (
            "at "
            + ", ".join(
                f"node $({i}, {j})$ (S = {two_step.stock[i][j]:.2f})" for i, j in early
            )
            if early
            else "nowhere with these inputs (try a higher $r$ or $K$)"
        )
        answer4 = (
            f"with the inputs above it is worth {two_step.value[0][0]:.4f}, and early "
            f"exercise happens {where}"
        )
    st.markdown(
        "4. **Price an American put on a two-step tree.  Where does early exercise happen?**  \n"
        f"   *Answer:* {answer4}.  Early exercise pays in the low nodes, where the interest on $K$ received "
        "now outweighs the remaining time value."
    )
    st.markdown(
        "5. **Why does the binomial price converge to the Black–Scholes price?**  \n"
        "   *Answer:* $\\ln S_T$ is a sum of $N$ independent steps, so by the central limit theorem it "
        "becomes Normal with the Black–Scholes mean and variance; see the **Continuous-time limit** tab."
    )

st.caption(
    "Cox, J.C., Ross, S.A. & Rubinstein, M. (1979). 'Option Pricing: A Simplified Approach.' "
    "Journal of Financial Economics, 7(3), 229–263. | "
    "Black, F. & Scholes, M. (1973). 'The Pricing of Options and Corporate Liabilities.' "
    "Journal of Political Economy, 81(3), 637–654."
)
