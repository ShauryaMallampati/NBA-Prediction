# PPO-LLM Strategy Shaping

**LLM-Guided Reward Shaping for Multi-Agent Coordination in Overcooked**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This repository contains the code for training PPO agents with LLM-based reward shaping in the Overcooked cooperative cooking environment. Our method uses a language model to evaluate joint actions and provide reward bonuses for cooperative behavior.

## Key Features

- **LLM-guided reward shaping**: Uses GPT-Neo to evaluate action cooperativeness
- **Multiple baselines**: Baseline PPO, CC_PPO, SP_PPO, HARL, PBT_PPO, PPO+LLM
- **Robustness evaluation**: Four perturbation regimes (No Noise, Noise, Delay, Combo)
- **Comprehensive analysis**: Nash gap, latency, robustness deltas, task completion

## Project Structure

```
PPO-LLM-Strategy-Shaping/
├── notebooks/
│   └── sim.ipynb              # Main experiment notebook
├── src/
│   └── ppo_llm_strategy_shaping/
│       ├── __init__.py        # Package exports
│       ├── config.py          # Configuration and hyperparameters
│       ├── env_wrappers.py    # Overcooked environment wrappers
│       ├── llm_shaping.py     # LLM reward shaping logic
│       ├── train.py           # Training loops and callbacks
│       ├── evaluation.py      # Nash gap, latency, robustness analysis
│       └── utils.py           # Utility functions
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ShauryaMallampati/PPO-LLM-Strategy-Shaping.git
cd PPO-LLM-Strategy-Shaping
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the Overcooked environment

```bash
git clone https://github.com/HumanCompatibleAI/overcooked_ai.git
pip install -e overcooked_ai
```

## Quick Start

### Using the Python API

```python
from ppo_llm_strategy_shaping import Config, train_all, run_nash_analysis

# Configure experiment
config = Config(
    layout="asymmetric_advantages",
    seeds=[1001, 2002, 3003],
    llm_model_name="EleutherAI/gpt-neo-1.3B",
)

# Train all baselines
results = train_all(config=config, n_jobs=10)

# Run Nash analysis
nash_df = run_nash_analysis(config=config)
```

### Using the Notebook

1. Open `notebooks/sim.ipynb` in Jupyter or Google Colab
2. Run the setup cells to install dependencies
3. Configure your experiment parameters
4. Execute training and evaluation cells

## Baselines

| Baseline | Description | Training Steps |
|----------|-------------|----------------|
| Baseline | Standard PPO | 1M |
| PPO+LLM | PPO with LLM reward shaping | 600K |
| CC_PPO | Centralized Critic PPO | 1M |
| SP_PPO | Self-Play PPO | 1M |
| HARL | Hierarchical Agent RL | 1M |
| PBT_PPO | Population-Based Training | 1M |

## Environment Perturbation Regimes

- **No Noise**: Clean environment (baseline)
- **Noise**: Gaussian noise (σ=0.01) added to observations
- **Delay**: 20% chance of reward penalty (-0.5) per step
- **Combo**: Combined noise and delay perturbations

## Configuration

Key parameters in `Config`:

```python
Config(
    layout="asymmetric_advantages",  # Overcooked layout
    horizon=400,                     # Episode length
    seeds=[1001, 2002, 3003, 4004, 5005],
    llm_model_name="EleutherAI/gpt-neo-1.3B",
    llm_bonus=0.2,                   # Reward bonus for "good" actions
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=2048,
)
```

## Results

Our experiments show that PPO+LLM:

- Achieves comparable performance to baselines with **40% fewer training steps**
- Demonstrates **improved robustness** under perturbations
- Has **lower Nash gap**, indicating better equilibrium approximation
- Maintains **real-time inference latency** suitable for deployment

## Citation

If you use this code, please cite:

```bibtex
@article{mallampati2025ppo_llm,
  title={LLM-Guided Reward Shaping for Multi-Agent Coordination},
  author={Mallampati, Shaurya},
  year={2025}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [HumanCompatibleAI/overcooked_ai](https://github.com/HumanCompatibleAI/overcooked_ai) for the Overcooked environment
- [Stable-Baselines3](https://stable-baselines3.readthedocs.io/) for PPO implementation
- [EleutherAI](https://www.eleuther.ai/) for GPT-Neo models

