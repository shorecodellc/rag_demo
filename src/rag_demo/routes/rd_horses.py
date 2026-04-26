# kevin fink
# kevin@shorecode.org
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException

from hp_filepaths import Files

router = APIRouter(prefix="/horses", tags=["horses"])

_files = Files()
_results_dir = _files.results_dir


def _read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"{path.name} not found — run backtest first.")
    df = pd.read_csv(path)
    df = df.where(pd.notna(df), None)
    return df.to_dict(orient="records")


@router.get("/metrics")
def get_metrics() -> dict:
    summary = pd.read_csv(_results_dir / "backtest_summary.csv")
    total_bets = int(summary["n_bets"].sum())
    weighted_roi = float((summary["roi"] * summary["n_bets"]).sum() / max(total_bets, 1))
    avg_hit = float((summary["hit_rate"] * summary["n_bets"]).sum() / max(total_bets, 1))
    avg_auc = float(summary["roc_auc"].mean())
    avg_brier = float(summary["brier"].mean())
    avg_ev = float(summary["avg_ev"].mean())
    return {
        "total_folds": len(summary),
        "total_bets": total_bets,
        "weighted_roi": round(weighted_roi, 4),
        "hit_rate": round(avg_hit, 4),
        "mean_auc": round(avg_auc, 4),
        "mean_brier": round(avg_brier, 4),
        "mean_ev": round(avg_ev, 4),
        "date_range": {
            "start": str(summary["test_start"].min()),
            "end": str(summary["test_end"].max()),
        },
    }


@router.get("/backtest-summary")
def get_backtest_summary() -> list[dict]:
    return _read_csv(_results_dir / "backtest_summary.csv")


@router.get("/feature-importance")
def get_feature_importance() -> list[dict]:
    return _read_csv(_results_dir / "feature_importance.csv")


@router.get("/top-picks")
def get_top_picks(limit: int = 100) -> list[dict]:
    path = _results_dir / "backtest_predictions.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="backtest_predictions.csv not found.")
    df = pd.read_csv(path)
    top = df[df["rank_in_race"] == 1].copy()
    top = top.sort_values("ev", ascending=False)
    cols = ["date", "raceno", "horse", "jockey", "trainer", "draw", "distance",
            "going", "venue", "field_size", "win_prob_norm", "ev", "target_win", "plc"]
    available = [c for c in cols if c in top.columns]
    top = top[available].head(limit)
    top = top.where(pd.notna(top), None)
    return top.to_dict(orient="records")


@router.get("/roi-by-fold")
def get_roi_by_fold() -> list[dict]:
    summary = pd.read_csv(_results_dir / "backtest_summary.csv")
    out = summary[["fold", "test_start", "roi", "roc_auc", "hit_rate", "n_bets", "avg_ev"]].copy()
    out = out.where(pd.notna(out), None)
    return out.to_dict(orient="records")
