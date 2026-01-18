"""
Training module for PPO-LLM Strategy Shaping experiments.

Provides training loops, callbacks, and parallel execution utilities
for running multi-agent RL experiments with various baselines.
"""

import os
import re
import json
import time
import csv
from typing import Optional, List, Tuple, Callable

import numpy as np
import torch

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback

from .config import Config, DEFAULT_CONFIG, BASELINES, ENV_NAMES
from .env_wrappers import make_env, make_train_env, warmup_mlam
from .utils import (
    set_global_seed,
    ensure_dir,
    get_run_dir,
    get_checkpoint_dir,
    get_model_path,
    find_latest_checkpoint,
    write_csv_header,
    append_csv_row,
)


class StopTrainingOnMaxSteps(BaseCallback):
    """
    Callback to stop training when a maximum number of timesteps is reached.
    
    Args:
        max_steps: Maximum number of timesteps before stopping
        verbose: Verbosity level (0=silent, 1=info)
    """
    
    def __init__(self, max_steps: int, verbose: int = 0):
        super().__init__(verbose=verbose)
        self.max_steps = max_steps

    def _on_step(self) -> bool:
        if self.num_timesteps >= self.max_steps:
            if self.verbose > 0:
                print(
                    f"Stopping training: timesteps ({self.num_timesteps}) "
                    f"reached limit ({self.max_steps})"
                )
            return False
        return True


class PBTCallback(BaseCallback):
    """
    Population-Based Training style callback for adaptive learning rate.
    
    Adjusts learning rate when performance plateaus.
    
    Args:
        check_freq: How often to check performance (in steps)
        verbose: Verbosity level
    """
    
    def __init__(self, check_freq: int = 5000, verbose: int = 0):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.best_mean_reward = -np.inf
        self.patience = 0

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:
            if len(self.model.ep_info_buffer) > 0:
                mean_reward = np.mean([
                    ep_info["r"] for ep_info in self.model.ep_info_buffer
                ])
            else:
                mean_reward = -np.inf
            
            if mean_reward <= self.best_mean_reward + 0.5:
                self.patience += 1
            else:
                self.best_mean_reward = mean_reward
                self.patience = 0
            
            if self.patience >= 2:
                old_lr = self.model.learning_rate
                new_lr = old_lr * np.random.choice([0.8, 1.2])
                self.model.learning_rate = new_lr
                for pg in self.model.policy.optimizer.param_groups:
                    pg["lr"] = new_lr
                self.patience = 0
        
        return True


def evaluate(
    agent: PPO,
    env,
    episodes: int = 10
) -> Tuple[float, float]:
    """
    Evaluate a trained agent over multiple episodes.
    
    Args:
        agent: Trained PPO agent
        env: Gymnasium environment
        episodes: Number of evaluation episodes
        
    Returns:
        Tuple of (mean_return, std_return)
    """
    scores = []
    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        ep_r = 0.0
        while not done:
            action, _ = agent.predict(obs, deterministic=True)
            obs, r, term, trunc, _ = env.step(action)
            done = term or trunc
            ep_r += float(r)
        scores.append(ep_r)
    
    return float(np.mean(scores)), float(np.std(scores))


def train_one_run(
    baseline: str,
    env_name: str,
    seed: int,
    config: Config = DEFAULT_CONFIG,
    steps_total: Optional[int] = None,
) -> Optional[Tuple[str, str, int, float]]:
    """
    Train a single experimental run.
    
    Args:
        baseline: Baseline method name (e.g., "PPO+LLM", "HARL")
        env_name: Environment perturbation regime
        seed: Random seed
        config: Configuration object
        steps_total: Total training steps (overrides config if provided)
        
    Returns:
        Tuple of (baseline, env_name, seed, mean_return) or None if already complete
    """
    set_global_seed(seed)
    
    # Determine total steps
    if steps_total is None:
        steps_total = config.baseline_steps.get(baseline, 1_000_000)
    
    label = f"{baseline}|{env_name}|{seed}"
    run_dir = get_run_dir(config.runs_dir, baseline, env_name, seed)
    ckpt_dir = get_checkpoint_dir(run_dir)
    
    ensure_dir(ckpt_dir)
    
    # Create environments
    train_env = make_train_env(baseline, config.layout, env_name, config.horizon)
    eval_env = make_env(env_name, config.layout, config.horizon)
    
    # Check if already complete
    final_path = get_model_path(run_dir)
    if os.path.exists(final_path):
        print(f"Skipping {label}: already has final_model.zip")
        return None
    
    # Try to resume from checkpoint
    agent = None
    reset_flag = True
    
    ckpt_path = find_latest_checkpoint(ckpt_dir)
    if ckpt_path:
        try:
            print(f"Resuming {label} from {ckpt_path}")
            agent = PPO.load(ckpt_path, env=train_env, device=config.device, verbose=1)
            reset_flag = False
        except Exception as e:
            print(f"Failed to load checkpoint: {e}. Starting fresh.")
            try:
                os.remove(ckpt_path)
            except OSError:
                pass
    
    # Create fresh agent if needed
    if agent is None:
        print(f"Starting fresh run: {label}")
        agent = PPO(
            "MlpPolicy",
            train_env,
            n_steps=config.n_steps,
            batch_size=config.batch_size,
            learning_rate=config.learning_rate,
            gamma=config.gamma,
            verbose=1,
            seed=seed,
            device=config.device,
        )
        reset_flag = True
    
    # Setup callbacks
    callbacks = [
        CheckpointCallback(
            save_freq=config.checkpoint_every_steps,
            save_path=ckpt_dir,
            name_prefix="ppo"
        ),
        StopTrainingOnMaxSteps(max_steps=steps_total, verbose=1),
    ]
    
    if baseline == "PBT_PPO":
        callbacks.append(PBTCallback(check_freq=10000))
    
    # Train
    t0 = time.time()
    agent.learn(
        total_timesteps=steps_total,
        callback=callbacks,
        reset_num_timesteps=reset_flag,
    )
    train_minutes = (time.time() - t0) / 60.0
    
    # Save final model
    agent.save(final_path)
    
    # Save metadata
    with open(os.path.join(run_dir, "meta.json"), "w") as f:
        json.dump({
            "baseline": baseline,
            "env": env_name,
            "seed": seed,
            "steps": steps_total,
            "layout": config.layout,
        }, f)
    
    # Evaluate
    mean_return, std_return = evaluate(agent, eval_env, config.eval_episodes)
    
    # Log to CSV
    append_csv_row(config.results_csv, [
        baseline, env_name, seed, "final",
        round(mean_return, 4), round(std_return, 4), round(train_minutes, 3)
    ])
    
    print(f"✅ [{label}] FINISH in {train_minutes:.2f} min | eval {mean_return:.2f}±{std_return:.2f}")
    
    return (baseline, env_name, seed, mean_return)


def train_all(
    baselines: List[str] = BASELINES,
    env_names: List[str] = ENV_NAMES,
    seeds: Optional[List[int]] = None,
    config: Config = DEFAULT_CONFIG,
    n_jobs: int = 20,
    use_parallel: bool = True,
) -> List[Tuple[str, str, int, float]]:
    """
    Run all training experiments.
    
    Args:
        baselines: List of baseline methods to train
        env_names: List of environment perturbation regimes
        seeds: List of random seeds (uses config.seeds if None)
        config: Configuration object
        n_jobs: Number of parallel jobs
        use_parallel: Whether to use joblib parallelization
        
    Returns:
        List of (baseline, env_name, seed, mean_return) tuples
    """
    if seeds is None:
        seeds = config.seeds
    
    # Initialize CSV
    write_csv_header(config.results_csv, [
        "baseline", "env", "seed", "phase",
        "mean_return", "std_dev", "train_minutes"
    ])
    
    # Prewarm MLAM to avoid pickle issues
    warmup_mlam(config.layout, config.horizon)
    
    # Build job list
    all_jobs = []
    for b in baselines:
        steps = config.baseline_steps.get(b, 1_000_000)
        for e in env_names:
            for s in seeds:
                all_jobs.append((b, e, s, steps))
    
    print(f"🚀 Launching {len(all_jobs)} training runs...")
    
    if use_parallel:
        from joblib import Parallel, delayed
        
        results = Parallel(n_jobs=n_jobs)(
            delayed(train_one_run)(b, e, s, config, steps)
            for b, e, s, steps in all_jobs
        )
    else:
        results = []
        for b, e, s, steps in all_jobs:
            result = train_one_run(b, e, s, config, steps)
            if result is not None:
                results.append(result)
    
    print("\n🎉 ALL RUNS COMPLETE.")
    return [r for r in results if r is not None]


def load_trained_model(
    baseline: str,
    env_name: str,
    seed: int,
    config: Config = DEFAULT_CONFIG,
) -> Optional[PPO]:
    """
    Load a trained model from disk.
    
    Args:
        baseline: Baseline method name
        env_name: Environment perturbation regime
        seed: Random seed
        config: Configuration object
        
    Returns:
        Loaded PPO model or None if not found
    """
    run_dir = get_run_dir(config.runs_dir, baseline, env_name, seed)
    model_path = get_model_path(run_dir)
    
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        return None
    
    # Create a dummy env for loading
    env = make_env(env_name, config.layout, config.horizon)
    
    return PPO.load(model_path, env=env, device=config.device)
