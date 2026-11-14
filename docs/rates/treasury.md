# Treasury yield curve

`quant_finance.rates.treasury` downloads US Treasury constant-maturity (CMT) yields from FRED and provides helpers for working with the curve.[^h15]

## What the numbers are

FRED's `DGS1MO` to `DGS30` series are the Federal Reserve's H.15 constant-maturity yields. Each is the **par yield** of a notional Treasury with exactly that maturity: the coupon rate at which that bond would price at par. The US Treasury interpolates them each day from the yields of the most recently issued (on-the-run) securities.[^treasury]

Every tenor is quoted on the same bond-equivalent basis, in percent, so the tenors are directly comparable. Bills are included on that basis too, unlike quotes on a discount basis such as Yahoo Finance's `^IRX`.

## Par yields are not discount rates

A par yield is not the rate for discounting a single cash flow at that maturity. That rate is the zero-coupon (spot) rate \(z(T)\), with discount factor \(P(T) = e^{-z(T)\,T}\) in this library's continuous compounding. Par yields \(y(T)\) and discount factors are linked by the par condition. For a bond with semi-annual coupons and maturity \(T\):

\[
1 = \frac{y(T)}{2}\sum_{k=1}^{2T} P\!\left(\tfrac{k}{2}\right) + P(T).
\]

Bootstrapping solves this one maturity at a time for \(P(T)\). The module does not do that yet, so use the par yields to describe the curve, not to price cash flows.

## Spreads

`yield_spread` returns long minus short tenor yields in percentage points, by default 10Y minus 2Y. A negative spread, an inverted curve, has preceded most US recessions since the 1960s,[^estrella] although the time between inversion and recession varies widely.

## References

[^h15]: Board of Governors of the Federal Reserve System. *Selected Interest Rates (Daily) – H.15*. Series available from FRED, Federal Reserve Bank of St. Louis.
[^treasury]: US Department of the Treasury. *Treasury Yield Curve Methodology*.
[^estrella]: Estrella, A. and Mishkin, F. S. (1998). Predicting U.S. recessions: financial variables as leading indicators. *Review of Economics and Statistics*, 80(1), 45–61.

## API

::: quant_finance.rates.treasury
