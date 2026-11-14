# Payoffs and strategies

`quant_finance.options.payoffs` gives the profit or loss at expiry of single options and of multi-leg strategies, net of the premium paid or received.

## Single options

For a terminal stock price \(S_T\), strike \(K\) and premium \(c\) (call) or \(p\) (put):

| Position | Profit at expiry | Break-even \(S_T\) |
|---|---|---|
| Long call | \(\max(S_T - K, 0) - c\) | \(K + c\) |
| Short call | \(c - \max(S_T - K, 0)\) | \(K + c\) |
| Long put | \(\max(K - S_T, 0) - p\) | \(K - p\) |
| Short put | \(p - \max(K - S_T, 0)\) | \(K - p\) |

The premium is not discounted: these are profits measured at expiry, as on a payoff diagram, and they ignore the interest that could be earned on the premium.

## Strategies

A strategy is a list of `OptionLeg`s, each an option type, a strike and a signed quantity (positive long, negative short), plus the net premium paid for the whole position:

\[
\text{profit}(S_T) = \sum_{i} q_i \max\!\left(\phi_i (S_T - K_i), 0\right) - \text{net premium}.
\]

Common examples, with \(K_1 < K_2 < K_3\):

| Strategy | Legs |
|---|---|
| Bull call spread | \(+1\) call \(K_1\), \(-1\) call \(K_2\) |
| Straddle | \(+1\) call \(K\), \(+1\) put \(K\) |
| Strangle | \(+1\) put \(K_1\), \(+1\) call \(K_2\) |
| Butterfly | \(+1\) call \(K_1\), \(-2\) calls \(K_2\), \(+1\) call \(K_3\), with \(K_2 = (K_1 + K_3)/2\) |

## API

::: quant_finance.options.payoffs
