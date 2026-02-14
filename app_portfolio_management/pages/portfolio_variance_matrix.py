import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Portfolio Variance and the Covariance Matrix",
    page_icon="💼",
    layout="wide",
)
st.header("Portfolio Variance and the Covariance Matrix")

st.write(
    "Linear algebra provides an elegant and computationally efficient way to calculate "
    "portfolio risk. Instead of writing out lengthy summation formulas, we can express "
    "portfolio variance using matrix notation, which scales effortlessly to any number of assets."
)

st.info(
    "The covariance matrix is central to Modern Portfolio Theory. It captures not only "
    "the individual volatilities of assets but also how they move together (covariance). "
    "Understanding matrix operations is essential for portfolio optimisation."
)


st.markdown("#### Why Linear Algebra in Portfolio Management?")

st.write("""
**Key applications of linear algebra in finance:**

1. **Portfolio variance calculation** — Express risk as a quadratic form: **w**ᵀ**Σw**
2. **Mean-variance optimisation** — Solve for optimal weights using matrix calculus
3. **Factor models** — Decompose returns into systematic factors using regression
4. **Risk decomposition** — Attribute portfolio risk to individual holdings
5. **Principal Component Analysis** — Identify key drivers of portfolio variance
""")


st.markdown("#### The Covariance Matrix")

st.write(
    "For a portfolio of $n$ assets, the covariance matrix **Σ** (sigma) is an $n \\times n$ "
    "symmetric matrix where each element $\\sigma_{ij}$ represents the covariance between "
    "asset $i$ and asset $j$."
)

with st.expander(label="Covariance Matrix Structure", expanded=True):
    latex_cov_matrix = r"""
        \boldsymbol{\Sigma} = \begin{bmatrix}
        \sigma_1^2 & \sigma_{12} & \sigma_{13} & \cdots & \sigma_{1n} \\
        \sigma_{21} & \sigma_2^2 & \sigma_{23} & \cdots & \sigma_{2n} \\
        \sigma_{31} & \sigma_{32} & \sigma_3^2 & \cdots & \sigma_{3n} \\
        \vdots & \vdots & \vdots & \ddots & \vdots \\
        \sigma_{n1} & \sigma_{n2} & \sigma_{n3} & \cdots & \sigma_n^2
        \end{bmatrix}
        """
    st.latex(latex_cov_matrix)

st.write("""
**Key properties of the covariance matrix:**
- **Diagonal elements** ($\\sigma_i^2$): Variance of each asset
- **Off-diagonal elements** ($\\sigma_{ij}$): Covariance between assets $i$ and $j$
- **Symmetric**: $\\sigma_{ij} = \\sigma_{ji}$ (covariance is commutative)
- **Positive semi-definite**: All eigenvalues are non-negative
""")


st.markdown("#### Portfolio Variance in Matrix Form")

st.write(
    "The portfolio variance can be expressed compactly using matrix multiplication:"
)

with st.expander(label="Portfolio Variance Formula", expanded=True):
    latex_port_var = r"""
        \sigma_p^2 = \mathbf{w}^\top \boldsymbol{\Sigma} \mathbf{w} \\ \\

        where: \\
        \mathbf{w} = \begin{bmatrix} w_1 \\ w_2 \\ \vdots \\ w_n \end{bmatrix}
        \text{ is the column vector of portfolio weights} \\ \\
        \boldsymbol{\Sigma} \text{ is the } n \times n \text{ covariance matrix} \\ \\
        \mathbf{w}^\top \text{ is the transpose of } \mathbf{w} \text{ (a row vector)}
        """
    st.latex(latex_port_var)

st.write("This single equation replaces the expanded summation form:")

with st.expander(label="Expanded Summation Form", expanded=False):
    latex_expanded = r"""
        \sigma_p^2 = \sum_{i=1}^{n} \sum_{j=1}^{n} w_i w_j \sigma_{ij}
        = \sum_{i=1}^{n} w_i^2 \sigma_i^2 + 2 \sum_{i=1}^{n} \sum_{j>i}^{n} w_i w_j \sigma_{ij}
        """
    st.latex(latex_expanded)


st.markdown("#### Interactive Three-Asset Example")

st.write(
    "Adjust the asset parameters and portfolio weights below to see how the covariance "
    "matrix and portfolio variance are calculated step by step."
)

st.markdown("##### Asset Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Asset A**")
    sigma_a = st.slider(
        "Volatility A (%)",
        min_value=5.0,
        max_value=40.0,
        value=15.0,
        step=1.0,
        key="sigma_a",
    )

with col2:
    st.markdown("**Asset B**")
    sigma_b = st.slider(
        "Volatility B (%)",
        min_value=5.0,
        max_value=40.0,
        value=20.0,
        step=1.0,
        key="sigma_b",
    )

with col3:
    st.markdown("**Asset C**")
    sigma_c = st.slider(
        "Volatility C (%)",
        min_value=5.0,
        max_value=40.0,
        value=25.0,
        step=1.0,
        key="sigma_c",
    )

st.markdown("##### Correlations")

col1, col2, col3 = st.columns(3)

with col1:
    rho_ab = st.slider(
        "Correlation A-B",
        min_value=-1.0,
        max_value=1.0,
        value=0.3,
        step=0.05,
        key="rho_ab",
    )

with col2:
    rho_ac = st.slider(
        "Correlation A-C",
        min_value=-1.0,
        max_value=1.0,
        value=0.1,
        step=0.05,
        key="rho_ac",
    )

with col3:
    rho_bc = st.slider(
        "Correlation B-C",
        min_value=-1.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        key="rho_bc",
    )

st.markdown("##### Portfolio Weights")

col1, col2, col3 = st.columns(3)

with col1:
    w_a = st.slider(
        "Weight A (%)",
        min_value=0.0,
        max_value=100.0,
        value=40.0,
        step=5.0,
        key="w_a",
    )

with col2:
    w_b = st.slider(
        "Weight B (%)",
        min_value=0.0,
        max_value=100.0,
        value=35.0,
        step=5.0,
        key="w_b",
    )

with col3:
    w_c = st.slider(
        "Weight C (%)",
        min_value=0.0,
        max_value=100.0,
        value=25.0,
        step=5.0,
        key="w_c",
    )

# Normalise weights
total_weight = w_a + w_b + w_c
if total_weight > 0:
    w_a_norm = w_a / total_weight
    w_b_norm = w_b / total_weight
    w_c_norm = w_c / total_weight
else:
    w_a_norm = w_b_norm = w_c_norm = 1 / 3

if abs(total_weight - 100) > 0.01:
    st.warning(
        f"Weights sum to {total_weight:.1f}%. "
        f"Normalised weights: A={w_a_norm:.1%}, B={w_b_norm:.1%}, C={w_c_norm:.1%}"
    )

# Convert to decimals
sigma_a_dec = sigma_a / 100
sigma_b_dec = sigma_b / 100
sigma_c_dec = sigma_c / 100

# Build covariance matrix
# Cov(i,j) = rho_ij * sigma_i * sigma_j
cov_aa = sigma_a_dec**2
cov_bb = sigma_b_dec**2
cov_cc = sigma_c_dec**2
cov_ab = rho_ab * sigma_a_dec * sigma_b_dec
cov_ac = rho_ac * sigma_a_dec * sigma_c_dec
cov_bc = rho_bc * sigma_b_dec * sigma_c_dec

covariance_matrix = np.array(
    [[cov_aa, cov_ab, cov_ac], [cov_ab, cov_bb, cov_bc], [cov_ac, cov_bc, cov_cc]]
)

correlation_matrix = np.array(
    [[1.0, rho_ab, rho_ac], [rho_ab, 1.0, rho_bc], [rho_ac, rho_bc, 1.0]]
)

weights = np.array([w_a_norm, w_b_norm, w_c_norm])


st.markdown("#### Step-by-Step Calculation")

st.markdown("##### Step 1: Construct the Covariance Matrix")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Correlation Matrix (ρ)**")
    fig1, ax1 = plt.subplots(figsize=(5, 4))
    im1 = ax1.imshow(correlation_matrix, cmap="RdBu_r", vmin=-1, vmax=1)
    ax1.set_xticks([0, 1, 2])
    ax1.set_yticks([0, 1, 2])
    ax1.set_xticklabels(["A", "B", "C"])
    ax1.set_yticklabels(["A", "B", "C"])
    for i in range(3):
        for j in range(3):
            ax1.text(j, i, f"{correlation_matrix[i, j]:.2f}", ha="center", va="center")
    plt.colorbar(im1, ax=ax1, label="Correlation")
    ax1.set_title("Correlation Matrix")
    st.pyplot(fig1)

with col2:
    st.markdown("**Covariance Matrix (Σ)**")
    fig2, ax2 = plt.subplots(figsize=(5, 4))
    im2 = ax2.imshow(covariance_matrix, cmap="YlOrRd")
    ax2.set_xticks([0, 1, 2])
    ax2.set_yticks([0, 1, 2])
    ax2.set_xticklabels(["A", "B", "C"])
    ax2.set_yticklabels(["A", "B", "C"])
    for i in range(3):
        for j in range(3):
            ax2.text(j, i, f"{covariance_matrix[i, j]:.4f}", ha="center", va="center")
    plt.colorbar(im2, ax=ax2, label="Covariance")
    ax2.set_title("Covariance Matrix")
    st.pyplot(fig2)

st.write(
    "**Covariance from correlation:** $\\sigma_{ij} = \\rho_{ij} \\cdot \\sigma_i \\cdot \\sigma_j$"
)


st.markdown("##### Step 2: Define the Weight Vector")

st.latex(rf"""
    \mathbf{{w}} = \begin{{bmatrix}} {w_a_norm:.4f} \\ {w_b_norm:.4f} \\ {w_c_norm:.4f} \end{{bmatrix}}
    \quad \text{{and}} \quad
    \mathbf{{w}}^\top = \begin{{bmatrix}} {w_a_norm:.4f} & {w_b_norm:.4f} & {w_c_norm:.4f} \end{{bmatrix}}
    """)


st.markdown("##### Step 3: Compute Σw (Matrix-Vector Multiplication)")

sigma_w = covariance_matrix @ weights

st.write("First, multiply the covariance matrix by the weight vector:")

st.latex(rf"""
    \boldsymbol{{\Sigma}} \mathbf{{w}} =
    \begin{{bmatrix}}
    {cov_aa:.4f} & {cov_ab:.4f} & {cov_ac:.4f} \\
    {cov_ab:.4f} & {cov_bb:.4f} & {cov_bc:.4f} \\
    {cov_ac:.4f} & {cov_bc:.4f} & {cov_cc:.4f}
    \end{{bmatrix}}
    \begin{{bmatrix}} {w_a_norm:.4f} \\ {w_b_norm:.4f} \\ {w_c_norm:.4f} \end{{bmatrix}}
    =
    \begin{{bmatrix}} {sigma_w[0]:.6f} \\ {sigma_w[1]:.6f} \\ {sigma_w[2]:.6f} \end{{bmatrix}}
    """)


st.markdown("##### Step 4: Compute wᵀΣw (Final Dot Product)")

portfolio_variance = weights @ sigma_w
portfolio_volatility = np.sqrt(portfolio_variance) * 100

st.write("Finally, take the dot product with the weight vector:")

st.latex(rf"""
    \sigma_p^2 = \mathbf{{w}}^\top (\boldsymbol{{\Sigma}} \mathbf{{w}}) =
    \begin{{bmatrix}} {w_a_norm:.4f} & {w_b_norm:.4f} & {w_c_norm:.4f} \end{{bmatrix}}
    \begin{{bmatrix}} {sigma_w[0]:.6f} \\ {sigma_w[1]:.6f} \\ {sigma_w[2]:.6f} \end{{bmatrix}}
    = {portfolio_variance:.6f}
    """)

st.latex(
    rf"\sigma_p = \sqrt{{{portfolio_variance:.6f}}} = {portfolio_volatility:.2f}\%"
)


st.markdown("#### Results Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Portfolio Variance", f"{portfolio_variance:.6f}")

with col2:
    st.metric("Portfolio Volatility", f"{portfolio_volatility:.2f}%")

with col3:
    # Calculate weighted average volatility (no diversification)
    weighted_avg_vol = w_a_norm * sigma_a + w_b_norm * sigma_b + w_c_norm * sigma_c
    diversification_benefit = weighted_avg_vol - portfolio_volatility
    st.metric(
        "Diversification Benefit",
        f"{diversification_benefit:.2f}%",
        help="Reduction in volatility compared to weighted average of individual volatilities",
    )


st.markdown("#### Verification: Expanded Formula")

st.write("We can verify our matrix calculation by expanding the summation manually:")

# Calculate each term
term_aa = (w_a_norm**2) * cov_aa
term_bb = (w_b_norm**2) * cov_bb
term_cc = (w_c_norm**2) * cov_cc
term_ab = 2 * w_a_norm * w_b_norm * cov_ab
term_ac = 2 * w_a_norm * w_c_norm * cov_ac
term_bc = 2 * w_b_norm * w_c_norm * cov_bc

verification_total = term_aa + term_bb + term_cc + term_ab + term_ac + term_bc

st.latex(r"""
    \sigma_p^2 = w_A^2 \sigma_A^2 + w_B^2 \sigma_B^2 + w_C^2 \sigma_C^2
    + 2 w_A w_B \sigma_{AB} + 2 w_A w_C \sigma_{AC} + 2 w_B w_C \sigma_{BC}
    """)

with st.expander("Show detailed calculation", expanded=False):
    st.write(
        f"$w_A^2 \\sigma_A^2 = {w_a_norm:.4f}^2 \\times {cov_aa:.4f} = {term_aa:.6f}$"
    )
    st.write(
        f"$w_B^2 \\sigma_B^2 = {w_b_norm:.4f}^2 \\times {cov_bb:.4f} = {term_bb:.6f}$"
    )
    st.write(
        f"$w_C^2 \\sigma_C^2 = {w_c_norm:.4f}^2 \\times {cov_cc:.4f} = {term_cc:.6f}$"
    )
    st.write(
        f"$2 w_A w_B \\sigma_{{AB}} = 2 \\times {w_a_norm:.4f} \\times {w_b_norm:.4f} "
        f"\\times {cov_ab:.4f} = {term_ab:.6f}$"
    )
    st.write(
        f"$2 w_A w_C \\sigma_{{AC}} = 2 \\times {w_a_norm:.4f} \\times {w_c_norm:.4f} "
        f"\\times {cov_ac:.4f} = {term_ac:.6f}$"
    )
    st.write(
        f"$2 w_B w_C \\sigma_{{BC}} = 2 \\times {w_b_norm:.4f} \\times {w_c_norm:.4f} "
        f"\\times {cov_bc:.4f} = {term_bc:.6f}$"
    )
    st.write(f"**Total: {verification_total:.6f}** ✓")


st.markdown("#### Key Insights")

st.write("""
**Why matrix notation matters:**

1. **Scalability** — The formula **w**ᵀ**Σw** works for any number of assets without rewriting
2. **Computational efficiency** — Matrix libraries (NumPy) are optimised for these operations
3. **Elegant notation** — Complex relationships expressed in compact form
4. **Foundation for optimisation** — Quadratic programming uses this form directly

**The covariance matrix captures:**
- Individual asset risks (diagonal)
- Pairwise relationships (off-diagonal)
- Diversification potential (low/negative correlations reduce portfolio risk)

**Practical note:** In real applications, estimating the covariance matrix from historical data
is challenging. Estimation error in the covariance matrix is a major source of portfolio
optimisation instability.
""")
