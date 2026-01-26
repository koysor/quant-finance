# quant-finance

This repository, `quant-finance`, serves as a comprehensive collection of Python code examples and tools for various quantitative finance applications. It encompasses modules dedicated to key areas such as fixed income analysis, options pricing and strategies, and portfolio management. The project aims to provide practical implementations of financial models and concepts, making complex quantitative methods accessible and understandable through code.

A significant feature of this repository is its integration with Streamlit, enabling users to interact with many of the quantitative finance tools via a user-friendly web application. This allows for immediate visualization and experimentation with financial models, from binomial trees for option pricing to Monte Carlo simulations for stock price forecasting. The Streamlit applications are structured around different financial domains, offering dedicated interfaces for each.

Beyond the interactive applications, the repository includes robust data ingestion capabilities, ensuring that the financial models can be fed with relevant and timely data. It also contains extensive unit tests to maintain code quality and accuracy, along with development configurations and Docker files to facilitate a consistent development and deployment environment. This makes `quant-finance` a valuable resource for both learning and applying quantitative finance principles.

## Live Streamlit Applications

This project features several Streamlit applications, providing interactive access to various quantitative finance tools.

*   **Streamlit Cloud:** A general overview application is available at: [https://maths-python-koysor.streamlit.app/](https://maths-python-koysor.streamlit.app/)

*   **AWS EC2 Deployments:** For more specialized applications, the following are deployed on an AWS EC2 instance. Please replace `YOUR_EC2_HOST` with the actual IP address or hostname of the EC2 instance where these applications are hosted.
    *   **Quant Finance:** `http://YOUR_EC2_HOST:8501`
    *   **Options:** `http://YOUR_EC2_HOST:8502`
    *   **Fixed Income:** `http://YOUR_EC2_HOST:8503`
    *   **Portfolio Management:** `http://YOUR_EC2_HOST:8504`
