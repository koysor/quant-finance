import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt


st.set_page_config(layout="wide")
st.markdown("### The Binomial Tree")


def binomial_tree(n: int, p: int) -> nx.DiGraph:
    """
    Generates a NetworkX binomial tree.

    Each node represents a state (level, successes).
    Each edge represents a transition with a probability.
    The tree is built level by level, where each node has two children:
    one for success and one for failure.
    The root node is (0, 0), representing the initial state with 0 successes.
    The tree is built until level n, where n is the number of trials.
    The probability of success is p, and the probability of failure is 1 - p.
    The function returns a directed graph (DiGraph) representing the binomial tree.

    Parameters:
    n (int): Number of trials.
    p (float): Probability of success.

    Returns:
    G (networkx.DiGraph): Directed graph representing the binomial tree.
    """
    G = nx.DiGraph()
    nodes = [(0, 0)]  # (level, successes)
    G.add_node((0, 0))

    while nodes:
        level, successes = nodes.pop(0)
        if level < n:
            # Probability of success
            next_success = (level + 1, successes + 1)
            G.add_edge((level, successes), next_success, probability=p)
            nodes.append(next_success)

            # Probability of failure
            next_failure = (level + 1, successes)
            G.add_edge((level, successes), next_failure, probability=1 - p)
            nodes.append(next_failure)

    return G


def display_binomial_tree(n, p):
    """Generates and displays the binomial tree using Matplotlib in Streamlit."""

    G = binomial_tree(n, p)
    st.write(G)
    pos = {}
    for node in G.nodes():
        level, successes = node
        pos[node] = (
            level,
            successes - level / 2,
        )  # Adjust y-position for better visualization

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


n = st.slider("Number of Trials (n)", min_value=1, max_value=5, value=2)
p = st.slider(
    "Probability of Success (p)", min_value=0.0, max_value=1.0, value=0.3, step=0.05
)

st.info(
    """
Each node is labeled (i, j) where:
- i = time step
- j = number of upward moves
- Nodes are arranged to show time progressing on the x-axis and states on the y-axis.
- Two edges per node: one for an up move and one for a down move.
        """
)
display_binomial_tree(n, p)
