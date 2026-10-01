"""Causal pregame feature helpers used by the supported ensemble pipeline."""

import pandas as pd


def calculate_elo(
    df: pd.DataFrame,
    k: int = 20,
    home_advantage: float = 100,
) -> pd.DataFrame:
    """Add Elo features, updating ratings only after each completed game."""
    df = df.sort_values("date").reset_index(drop=True)
    ratings: dict[str, float] = {}
    default_elo = 1500.0
    home_values, away_values, differences, probabilities = [], [], [], []

    for _, row in df.iterrows():
        home, away, home_win = row["home"], row["away"], row["home_win"]
        home_elo = ratings.get(home, default_elo)
        away_elo = ratings.get(away, default_elo)
        probability = 1 / (
            1 + 10 ** ((away_elo - home_elo - home_advantage) / 400)
        )

        home_values.append(home_elo)
        away_values.append(away_elo)
        differences.append(home_elo - away_elo + home_advantage)
        probabilities.append(probability)

        if pd.notna(home_win):
            ratings[home] = home_elo + k * (home_win - probability)
            ratings[away] = away_elo + k * ((1 - home_win) - (1 - probability))

    df["elo_home"] = home_values
    df["elo_away"] = away_values
    df["elo_diff"] = differences
    df["elo_win_prob"] = probabilities
    df["elo_p_home"] = df["elo_home"] / (df["elo_home"] + df["elo_away"])
    df["home_adv_flag"] = 1
    df["home_court_adv"] = home_advantage
    return df


def add_rest_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add rest features using only games strictly earlier in row order."""
    df = df.sort_values("date").reset_index(drop=True)
    last_game: dict[str, pd.Timestamp] = {}
    home_rest, away_rest = [], []

    for _, row in df.iterrows():
        home, away = row["home"], row["away"]
        game_date = pd.to_datetime(row["date"])
        home_days = (game_date - last_game.get(home, game_date - pd.Timedelta(days=3))).days
        away_days = (game_date - last_game.get(away, game_date - pd.Timedelta(days=3))).days
        home_rest.append(min(home_days, 7))
        away_rest.append(min(away_days, 7))
        last_game[home] = game_date
        last_game[away] = game_date

    df["home_rest_days"] = home_rest
    df["away_rest_days"] = away_rest
    df["rest_differential"] = df["home_rest_days"] - df["away_rest_days"]
    df["home_rest_advantage"] = (
        df["home_rest_days"] > df["away_rest_days"]
    ).astype(int)
    df["away_rest_advantage"] = (
        df["away_rest_days"] > df["home_rest_days"]
    ).astype(int)
    df["home_back_to_back"] = (df["home_rest_days"] <= 1).astype(int)
    df["away_back_to_back"] = (df["away_rest_days"] <= 1).astype(int)
    return df


def add_streak_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add win/loss streaks, updating state only after each completed game."""
    df = df.sort_values("date").reset_index(drop=True)
    win_streaks: dict[str, int] = {}
    loss_streaks: dict[str, int] = {}
    home_win, away_win, home_loss, away_loss = [], [], [], []

    for _, row in df.iterrows():
        home, away = row["home"], row["away"]
        home_win.append(win_streaks.get(home, 0))
        away_win.append(win_streaks.get(away, 0))
        home_loss.append(loss_streaks.get(home, 0))
        away_loss.append(loss_streaks.get(away, 0))

        if pd.isna(row["home_win"]):
            continue
        if row["home_win"] == 1:
            win_streaks[home] = win_streaks.get(home, 0) + 1
            loss_streaks[home] = 0
            win_streaks[away] = 0
            loss_streaks[away] = loss_streaks.get(away, 0) + 1
        else:
            win_streaks[home] = 0
            loss_streaks[home] = loss_streaks.get(home, 0) + 1
            win_streaks[away] = win_streaks.get(away, 0) + 1
            loss_streaks[away] = 0

    df["home_win_streak"] = home_win
    df["away_win_streak"] = away_win
    df["home_loss_streak"] = home_loss
    df["away_loss_streak"] = away_loss
    return df
