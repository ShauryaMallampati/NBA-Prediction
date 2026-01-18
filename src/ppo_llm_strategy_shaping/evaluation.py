"""
Evaluation module for PPO-LLM Strategy Shaping experiments.

Provides evaluation utilities including:
- Nash gap computation via best-response training
- Latency measurement
- Robustness delta analysis
- Task completion metrics
"""

import os
import time
import csv
from typing import Optional, Tuple, List, Dict, Any

import numpy as np
import pandas as pd
import gymnasium as gym

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

from .config import Config, DEFAULT_CONFIG, BASELINES, ENV_NAMES
from .env_wrappers import make_env, OCWrapper, NUM_ACTIONS
from .utils import (
    set_global_seed,
    get_run_dir,
    get_model_path,
    write_csv_header,
    append_csv_row,
    load_completed_set,
    ensure_dir,
)


# =============================================================================
# Basic Evaluation
# =============================================================================

def evaluate(
    agent: PPO,
    env: gym.Env,
    episodes: int = 10,
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


# =============================================================================
# Nash Gap / Best Response Analysis
# =============================================================================

class BestResponseEnv(gym.Env):
    """
    Environment for training a best response against a fixed opponent.
    
    Creates a single-agent MDP where one agent's policy is fixed
    and the other agent learns.
    
    Args:
        env_name: Environment perturbation regime
        layout: Overcooked layout name
        opponent_model: Fixed opponent PPO model
        agent_idx: Index of the learning agent (0 or 1)
        horizon: Maximum episode length
    """
    
    def __init__(
        self,
        env_name: str,
        layout: str,
        opponent_model: PPO,
        agent_idx: int,
        horizon: int = 400,
    ):
        super().__init__()
        self.agent_idx = agent_idx
        self.opponent_idx = 1 - agent_idx
        self.opponent_model = opponent_model
        
        self.base_env = make_env(env_name, layout, horizon).env
        self.observation_space = self.base_env.observation_space
        self.action_space = gym.spaces.Discrete(NUM_ACTIONS)
        self._last_obs = None

    def reset(self, seed=None, options=None):
        if seed is not None:
            set_global_seed(seed)
        obs, info = self.base_env.reset(seed=seed)
        self._last_obs = obs
        return obs, info

    def step(self, action):
        a_self = int(action)
        
        # Get opponent action from fixed policy
        opp_joint, _ = self.opponent_model.predict(self._last_obs, deterministic=True)
        a_opp = int(opp_joint[self.opponent_idx])
        
        # Construct joint action
        joint = np.zeros(2, dtype=np.int64)
        joint[self.agent_idx] = a_self
        joint[self.opponent_idx] = a_opp
        
        obs, r, term, trunc, info = self.base_env.step(joint)
        self._last_obs = obs
        return obs, float(r), bool(term), bool(trunc), info


def train_best_response(
    env_name: str,
    layout: str,
    opponent_model: PPO,
    agent_idx: int,
    seed: int,
    train_steps: int = 200_000,
    eval_episodes: int = 20,
    device: str = "cuda",
) -> Tuple[float, float]:
    """
    Train a best response agent against a fixed opponent.
    
    Args:
        env_name: Environment perturbation regime
        layout: Overcooked layout name
        opponent_model: Fixed opponent policy
        agent_idx: Index of learning agent (0 or 1)
        seed: Random seed
        train_steps: Total training timesteps
        eval_episodes: Evaluation episodes
        device: Compute device
        
    Returns:
        Tuple of (mean_return, std_return) for the best response
    """
    set_global_seed(seed)
    
    br_env = Monitor(BestResponseEnv(
        env_name, layout, opponent_model, agent_idx
    ))
    
    br = PPO(
        "MlpPolicy",
        br_env,
        n_steps=2048,
        batch_size=2048,
        learning_rate=3e-4,
        gamma=0.99,
        verbose=0,
        device=device,
        seed=seed,
    )
    
    br.learn(total_timesteps=train_steps)
    
    # Evaluate
    scores = []
    for _ in range(eval_episodes):
        obs, _ = br_env.reset()
        ep = 0
        done = False
        while not done:
            a, _ = br.predict(obs, deterministic=True)
            obs, r, term, trunc, _ = br_env.step(a)
            done = term or trunc
            ep += r
        scores.append(ep)
    
    return float(np.mean(scores)), float(np.std(scores))


def compute_nash_gap(
    baseline: str,
    env_name: str,
    seed: int,
    config: Config = DEFAULT_CONFIG,
) -> Optional[Dict[str, Any]]:
    """
    Compute the Nash gap for a trained model.
    
    Nash gap = V(BR) - V(self-play)
    where V(BR) is the value of the best response against the policy.
    
    Args:
        baseline: Baseline method name
        env_name: Environment perturbation regime
        seed: Random seed
        config: Configuration object
        
    Returns:
        Dictionary with Nash analysis results or None if model not found
    """
    run_dir = get_run_dir(config.runs_dir, baseline, env_name, seed)
    model_path = get_model_path(run_dir)
    
    if not os.path.exists(model_path):
        print(f"Missing model: {model_path}")
        return None
    
    model = PPO.load(model_path, device=config.device)
    
    # Self-play evaluation
    env_self = make_env(env_name, config.layout, config.horizon)
    v_self_m, v_self_s = evaluate(model, env_self, config.br_eval_episodes)
    
    # Best response evaluation
    v_br_m, v_br_s = train_best_response(
        env_name,
        config.layout,
        model,
        agent_idx=0,
        seed=seed + 999,
        train_steps=config.br_train_steps,
        eval_episodes=config.br_eval_episodes,
        device=config.device,
    )
    
    return {
        "baseline": baseline,
        "env": env_name,
        "seed": seed,
        "V_self_mean": v_self_m,
        "V_self_std": v_self_s,
        "V_BR_mean": v_br_m,
        "V_BR_std": v_br_s,
        "delta": v_br_m - v_self_m,
    }


def run_nash_analysis(
    baselines: List[str] = BASELINES,
    env_names: List[str] = ENV_NAMES,
    seeds: Optional[List[int]] = None,
    config: Config = DEFAULT_CONFIG,
    n_jobs: int = 6,
) -> pd.DataFrame:
    """
    Run Nash gap analysis for all configurations.
    
    Args:
        baselines: List of baseline methods
        env_names: List of environment regimes
        seeds: List of random seeds
        config: Configuration object
        n_jobs: Number of parallel jobs
        
    Returns:
        DataFrame with Nash analysis results
    """
    from joblib import Parallel, delayed
    from .env_wrappers import warmup_mlam
    
    if seeds is None:
        seeds = config.seeds
    
    # Prewarm MLAM
    warmup_mlam(config.layout, config.horizon)
    
    # Initialize CSV
    write_csv_header(config.br_results_csv, [
        "baseline", "env", "seed",
        "V_self_mean", "V_self_std",
        "V_BR_mean", "V_BR_std", "delta"
    ])
    
    # Get completed runs
    completed = load_completed_set(config.br_results_csv)
    
    # Build job list
    jobs = [
        (b, e, s) for b in baselines for e in env_names for s in seeds
        if (b, e, str(s)) not in completed
    ]
    
    print(f"Remaining Nash analysis jobs: {len(jobs)}")
    
    def wrapper(job):
        res = compute_nash_gap(*job, config)
        if res is None:
            return None
        
        append_csv_row(config.br_results_csv, [
            res["baseline"], res["env"], res["seed"],
            round(res["V_self_mean"], 2), round(res["V_self_std"], 2),
            round(res["V_BR_mean"], 2), round(res["V_BR_std"], 2),
            round(res["delta"], 2),
        ])
        print(f"Saved: {job}")
        return res
    
    results = Parallel(n_jobs=n_jobs)(delayed(wrapper)(job) for job in jobs)
    
    print(f"Nash analysis complete. Saved to: {config.br_results_csv}")
    
    # Return as DataFrame
    return pd.read_csv(config.br_results_csv)


# =============================================================================
# Latency Measurement
# =============================================================================

def measure_latency(
    agent: PPO,
    env: gym.Env,
    episodes: int = 5,
) -> float:
    """
    Measure average latency per decision step (predict + env.step) in milliseconds.
    
    Args:
        agent: Trained PPO agent
        env: Gymnasium environment
        episodes: Number of episodes for measurement
        
    Returns:
        Average latency in milliseconds per step
    """
    total_time = 0.0
    total_steps = 0
    
    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        
        while not done:
            t0 = time.perf_counter()
            
            action, _ = agent.predict(obs, deterministic=True)
            obs, r, term, trunc, _ = env.step(action)
            
            t1 = time.perf_counter()
            
            total_time += (t1 - t0)
            total_steps += 1
            done = term or trunc
    
    if total_steps == 0:
        return float("nan")
    
    return (total_time / total_steps) * 1000.0


def run_latency_sweep(
    baselines: List[str] = BASELINES,
    env_names: List[str] = ENV_NAMES,
    seeds: Optional[List[int]] = None,
    config: Config = DEFAULT_CONFIG,
    episodes_per_model: int = 5,
) -> pd.DataFrame:
    """
    Measure latency for all trained models.
    
    Args:
        baselines: List of baseline methods
        env_names: List of environment regimes
        seeds: List of random seeds
        config: Configuration object
        episodes_per_model: Episodes per measurement
        
    Returns:
        DataFrame with latency results
    """
    if seeds is None:
        seeds = config.seeds
    
    rows = []
    
    print("=== Measuring per-step latency for all models ===")
    
    for b in baselines:
        for e in env_names:
            seed_latencies = []
            
            for s in seeds:
                run_dir = get_run_dir(config.runs_dir, b, e, s)
                model_path = get_model_path(run_dir)
                
                if not os.path.exists(model_path):
                    print(f"[WARN] Missing model: {model_path}")
                    continue
                
                env = make_env(e, config.layout, config.horizon)
                agent = PPO.load(model_path, env=env, device=config.device)
                
                # Warmup
                for _ in range(10):
                    obs, _ = env.reset()
                    action, _ = agent.predict(obs, deterministic=True)
                    obs, _, term, trunc, _ = env.step(action)
                    if term or trunc:
                        break
                
                lat = measure_latency(agent, env, episodes=episodes_per_model)
                
                if not np.isnan(lat):
                    rows.append([b, e, s, lat])
                    seed_latencies.append(lat)
                    print(f"{b} | {e} | seed={s}: {lat:.4f} ms/step")
            
            if seed_latencies:
                mean_lat = float(np.mean(seed_latencies))
                std_lat = float(np.std(seed_latencies))
                print(f"[AGG] {b} | {e}: {mean_lat:.4f} ± {std_lat:.4f} ms/step")
                rows.append([b, e, "mean_over_seeds", mean_lat])
                rows.append([b, e, "std_over_seeds", std_lat])
    
    # Save CSV
    ensure_dir(os.path.dirname(config.latency_csv))
    with open(config.latency_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["baseline", "env", "seed_or_stat", "latency_ms"])
        writer.writerows(rows)
    
    print(f"\nLatency sweep complete. Saved to: {config.latency_csv}")
    
    return pd.read_csv(config.latency_csv)


# =============================================================================
# Robustness Delta Analysis
# =============================================================================

def compute_robustness_deltas(
    config: Config = DEFAULT_CONFIG,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute robustness deltas from training results.
    
    Robustness delta = V(No Noise) - V(perturbed env)
    Lower deltas indicate more robust policies.
    
    Args:
        config: Configuration object
        
    Returns:
        Tuple of (per_seed_df, aggregated_df)
    """
    print(f"Loading training results from: {config.results_csv}")
    df = pd.read_csv(config.results_csv)
    
    # Filter to final policies
    df_final = df[df["phase"] == "final"].copy()
    
    # Normalize environment names
    df_final["env_norm"] = df_final["env"].str.strip().str.lower()
    
    env_map = {
        "no noise": "No Noise",
        "noise": "Noise",
        "delay": "Delay",
        "combo": "Combo",
    }
    df_final["env_clean"] = df_final["env_norm"].map(env_map)
    
    # Group and pivot
    grouped = df_final.groupby(
        ["baseline", "env_clean", "seed"], as_index=False
    )["mean_return"].mean()
    
    pivot = grouped.pivot_table(
        index=["baseline", "seed"],
        columns="env_clean",
        values="mean_return"
    ).reset_index()
    
    # Ensure all columns exist
    for col in ["No Noise", "Noise", "Delay", "Combo"]:
        if col not in pivot.columns:
            pivot[col] = np.nan
    
    # Compute deltas
    pivot["delta_noise"] = pivot["No Noise"] - pivot["Noise"]
    pivot["delta_delay"] = pivot["No Noise"] - pivot["Delay"]
    pivot["delta_combo"] = pivot["No Noise"] - pivot["Combo"]
    
    # Save per-seed results
    per_seed_cols = [
        "baseline", "seed",
        "No Noise", "Noise", "Delay", "Combo",
        "delta_noise", "delta_delay", "delta_combo",
    ]
    per_seed_df = pivot[per_seed_cols]
    per_seed_df.to_csv(config.robustness_per_seed_csv, index=False)
    print(f"Saved per-seed robustness deltas to: {config.robustness_per_seed_csv}")
    
    # Aggregate over seeds
    agg_rows = []
    for b, sub in pivot.groupby("baseline"):
        row = {
            "baseline": b,
            "V_no_noise_mean": sub["No Noise"].mean(),
            "V_no_noise_std": sub["No Noise"].std(),
            "V_noise_mean": sub["Noise"].mean(),
            "V_noise_std": sub["Noise"].std(),
            "V_delay_mean": sub["Delay"].mean(),
            "V_delay_std": sub["Delay"].std(),
            "V_combo_mean": sub["Combo"].mean(),
            "V_combo_std": sub["Combo"].std(),
            "delta_noise_mean": sub["delta_noise"].mean(),
            "delta_noise_std": sub["delta_noise"].std(),
            "delta_delay_mean": sub["delta_delay"].mean(),
            "delta_delay_std": sub["delta_delay"].std(),
            "delta_combo_mean": sub["delta_combo"].mean(),
            "delta_combo_std": sub["delta_combo"].std(),
        }
        agg_rows.append(row)
    
    agg_df = pd.DataFrame(agg_rows)
    agg_df.to_csv(config.robustness_agg_csv, index=False)
    print(f"Saved aggregated robustness stats to: {config.robustness_agg_csv}")
    
    return per_seed_df, agg_df


# =============================================================================
# Task Completion Analysis
# =============================================================================

def compute_task_completion(
    config: Config = DEFAULT_CONFIG,
    r_min: float = -40.0,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute task completion metrics based on sparse rewards.
    
    Args:
        config: Configuration object
        r_min: Minimum reward floor (penalty floor)
        
    Returns:
        Tuple of (per_seed_df, aggregated_df)
    """
    print(f"Loading training results from: {config.results_csv}")
    df = pd.read_csv(config.results_csv)
    
    # Filter to final policies
    df_final = df[df["phase"] == "final"].copy()
    df_final["env_clean"] = df_final["env"].str.strip()
    
    # Group
    grouped = df_final.groupby(
        ["baseline", "env_clean", "seed"], as_index=False
    ).agg(
        mean_return=("mean_return", "mean"),
        std_return=("mean_return", "std"),
        mean_std_dev=("std_dev", "mean"),
    )
    
    # Compute completion metrics
    grouped["completion_score"] = grouped["mean_return"] - r_min
    grouped["completion_norm"] = grouped["completion_score"] / abs(r_min)
    
    # Save per-seed
    grouped.to_csv(config.task_per_seed_csv, index=False)
    print(f"Saved per-seed task completion metrics to: {config.task_per_seed_csv}")
    
    # Aggregate
    agg = grouped.groupby(
        ["baseline", "env_clean"], as_index=False
    ).agg(
        mean_return_mean=("mean_return", "mean"),
        mean_return_std=("mean_return", "std"),
        completion_score_mean=("completion_score", "mean"),
        completion_score_std=("completion_score", "std"),
        completion_norm_mean=("completion_norm", "mean"),
        completion_norm_std=("completion_norm", "std"),
    )
    
    agg.to_csv(config.task_agg_csv, index=False)
    print(f"Saved aggregated task completion metrics to: {config.task_agg_csv}")
    
    return grouped, agg
