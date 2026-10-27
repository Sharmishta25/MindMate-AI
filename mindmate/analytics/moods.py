"""Descriptive statistics only; missing days are never scored as zero."""
import numpy as np
import pandas as pd


def summarize(rows, start, end):
    start, end = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    if start > end:
        raise ValueError("Start date must be on or before end date")
    df = pd.DataFrame(rows)
    empty = pd.DataFrame(columns=["date", "mean_mood", "check_ins"])
    if df.empty:
        return {"count": 0, "recent": None, "average": None, "daily": empty, "weekly": empty.copy()}
    df["date"] = pd.to_datetime(df["entry_date"], format="%Y-%m-%d")
    df = df[df["date"].between(start, end)].sort_values(["date", "id"])
    if df.empty:
        return {"count": 0, "recent": None, "average": None, "daily": empty, "weekly": empty.copy()}
    daily = df.groupby("date")["mood_score"].agg(mean_mood="mean", check_ins="count").reset_index()
    df["week"] = df["date"] - pd.to_timedelta(df["date"].dt.weekday, unit="D")
    weekly = df.groupby("week")["mood_score"].agg(mean_mood="mean", check_ins="count").reset_index().rename(columns={"week": "date"})
    return {"count": len(df), "recent": int(df.iloc[-1]["mood_score"]),
            "average": float(np.mean(df["mood_score"].to_numpy())), "daily": daily, "weekly": weekly}
