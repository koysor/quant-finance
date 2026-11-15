# Launching the Streamlit apps on Windows

The `launch_*.sh` scripts are bash scripts. On Windows, run them from PowerShell through Git Bash.[^linux] First `cd` into your `quant-finance` clone. Each script changes to its own folder before it starts, so the relative path below is enough.

> Use the full path to Git's `bash.exe`. A bare `bash` can start WSL (`C:\Windows\System32\bash.exe`), which doesn't use this repo's Windows `.venv` or `uv`.

## Quantitative Finance

```powershell
& "C:\Program Files\Git\bin\bash.exe" .\launch_quantfinance_streamlit_app.sh
```

## Options

```powershell
& "C:\Program Files\Git\bin\bash.exe" .\launch_options_streamlit_app.sh
```

## Fixed Income

```powershell
& "C:\Program Files\Git\bin\bash.exe" .\launch_fixed_income_streamlit_app.sh
```

## Portfolio Management

```powershell
& "C:\Program Files\Git\bin\bash.exe" .\launch_portfolio_management_streamlit_app.sh
```

## Notes

- The app opens at http://localhost:8501.
- Extra arguments go to Streamlit. For example, add `--server.port 8502` to the end of the command to run a second app alongside the first.

[^linux]: On Linux (and macOS), run the scripts directly from a terminal in the `quant-finance` folder, for example `./launch_quantfinance_streamlit_app.sh`. If you get `Permission denied`, make them executable once with `chmod +x launch_*.sh`, or run one with `bash launch_quantfinance_streamlit_app.sh`.
