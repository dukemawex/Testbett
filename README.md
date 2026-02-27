# Sportsbook Research/Forecast/Execution Framework

# Project Structure:

```
/.github/
    workflows/
        scheduler.yml
/src/
    research/
        models/
            execution/
            storage/
/config/
    settings.py
    constants.py
    logging.yaml
/data/
    .gitkeep
/tests/
    test_poisson.py
    test_kelly.py
    test_true_probability.py
README.md
requirements.txt
```

## Explanations
This repository consists of a DRY_RUN sportsbook framework that allows for simulation of bets, forecasting, and execution logic without actually executing trades.

The framework is designed to run every two hours, gathering and forecasting data to write into a CSV file.

### Installation
Run the following command to install the required dependencies:
```
pip install -r requirements.txt
```

### Usage
To run the framework:
```
python src/main.py
```

### Safety Notes
Make sure to run in DRY_RUN mode by default. Sometimes live execution may be needed but it's locked behind an environment variable and secret check.

### Secrets
Ensure secrets are stored securely using GitHub Secrets and accessible as environment variables during execution.