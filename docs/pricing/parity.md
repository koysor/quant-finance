# Put-call parity

`quant_finance.pricing.parity` uses put-call parity to check prices and to infer one option's price from the other's.[^stoll]

## The relationship

For a European call and put with the same strike \(K\) and expiry \(T\), on a stock with continuous dividend yield \(q\):

\[
C + K e^{-rT} = P + S e^{-qT}.
\]

## Why it holds

Compare two portfolios:

- **A:** one call, plus cash of \(K e^{-rT}\) invested at the risk-free rate.
- **B:** one put, plus \(e^{-qT}\) shares, with dividends reinvested in the stock.

At expiry both are worth \(\max(S_T, K)\): if \(S_T > K\) each holds a stock worth \(S_T\), and otherwise each holds \(K\). Portfolios with the same payoff in every state must cost the same today, or buying the cheaper one and selling the dearer one is an arbitrage.

The argument uses no model: there is no volatility and no distribution of \(S_T\). It needs only European exercise, no frictions, and borrowing and lending at \(r\).

## Uses

- `parity_difference` returns \((C + K e^{-rT}) - (P + S e^{-qT})\). A value far from zero, beyond bid-ask spreads and borrowing costs, points to an arbitrage or bad data.
- `implied_call` and `implied_put` rearrange parity to price one option from the other.
- For American options on a stock without dividends, parity becomes a pair of inequalities, \(S - K \le C - P \le S - K e^{-rT}\), and these functions do not apply.

## References

[^stoll]: Stoll, H. R. (1969). The relationship between put and call option prices. *Journal of Finance*, 24(5), 801–824.

## API

::: quant_finance.pricing.parity
