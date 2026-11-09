import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(page_title="The Binomial Tree", page_icon="📊", layout="wide")
st.header("The Binomial Tree")


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
    """Generates and displays the binomial tree using Matplotlib in Streamlit."""

    G = binomial_tree(n, p)
    pos = {}
    for node in G.nodes():
        level, successes = node
        pos[node] = (
            level,
            successes - level / 2,
        )  # Adjust y-position for better visualisation

    edge_labels = nx.get_edge_attributes(G, "probability")
    formatted_edge_labels = {k: f"{v:.2f}" for k, v in edge_labels.items()}

    fig, ax = plt.subplots()
    nx.draw(
        G,
        pos,
        with_labels=True,
        node_size=800,
        node_color="lightblue",
        font_size=8,
        font_weight="bold",
        ax=ax,
    )
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=formatted_edge_labels, font_size=8, label_pos=0.3, ax=ax
    )
    ax.set_title(f"Binomial Tree (n={n}, p={p})")
    ax.set_xlabel("Level")
    ax.set_ylabel("Number of Successes")
    st.pyplot(fig)
    plt.close(fig)


n = st.slider("Number of Trials (n)", min_value=1, max_value=5, value=2)
p = st.slider(
    "Probability of Success (p)", min_value=0.0, max_value=1.0, value=0.3, step=0.05
)

st.info("""
Each node is labeled (i, j) where:
- i = time step
- j = number of upward moves
- Nodes are arranged to show time progressing on the x-axis and states on the y-axis.
- Two edges per node: one for an up move and one for a down move.
        """)
display_binomial_tree(n, p)

st.caption(
    "Cox, J.C., Ross, S.A. & Rubinstein, M. (1979). 'Option Pricing: A Simplified Approach.' "
    "Journal of Financial Economics, 7(3), 229–263."
)
