# quant-finance

This repository, `quant-finance`, serves as a comprehensive collection of Python code examples and tools for various quantitative finance applications. It encompasses modules dedicated to key areas such as fixed income analysis, options pricing and strategies, and portfolio management. The project aims to provide practical implementations of financial models and concepts, making complex quantitative methods accessible and understandable through code.

A significant feature of this repository is its integration with Streamlit, enabling users to interact with many of the quantitative finance tools via a user-friendly web application. This allows for immediate visualization and experimentation with financial models, from binomial trees for option pricing to Monte Carlo simulations for stock price forecasting. The Streamlit applications are structured around different financial domains, offering dedicated interfaces for each.

Beyond the interactive applications, the repository includes robust data ingestion capabilities, ensuring that the financial models can be fed with relevant and timely data. It also contains extensive unit tests to maintain code quality and accuracy, along with development configurations and Docker files to facilitate a consistent development and deployment environment. This makes `quant-finance` a valuable resource for both learning and applying quantitative finance principles.

## Live Streamlit Applications

This project features several Streamlit applications, providing interactive access to various quantitative finance tools.

* **AWS EC2 Deployments:** For more specialised applications, the following are deployed on an AWS EC2 instance.

  * **Quant Finance:** http://koysor.duckdns.org/
  * **Options:** http://koysor.duckdns.org/options/
  * **Fixed Income:** http://koysor.duckdns.org/fixed-income/
  * **Portfolio Management:** http://koysor.duckdns.org/portfolio/

## Interactive Marimo Notebooks

Interactive Python notebooks are available via GitHub Pages at **https://koysor.github.io/quant-finance/**

These notebooks run entirely in your browser using WebAssembly (no server required) and allow you to view, edit, and execute the code directly:

* [Distributions: Normal vs Lognormal](https://koysor.github.io/quant-finance/distributions_normal_vs_lognormal.html)
* [Simulate Geometric Brownian Motion Paths](https://koysor.github.io/quant-finance/simulate_geometric_brownian_motion_paths.html)
* [S&amp;P 500 Data Ingestion](https://koysor.github.io/quant-finance/sp500_data_ingestion.html)
* [YFinance Index Prices](https://koysor.github.io/quant-finance/yfinance_index_prices.html)
