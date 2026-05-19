from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import os
from pathlib import Path
from typing import Iterable, Sequence

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib"))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.font_manager import FontProperties, findfont
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter


DEFAULT_EVENT_STATS = [
    ("Chronic Bronchitis", 1.31, 1.18, 1.45),
    ("COPD Exacerbation", 1.48, 1.33, 1.64),
    ("Lung Cancer", 2.96, 2.60, 3.33),
    ("Ischemic Stroke", 1.27, 1.14, 1.40),
    ("Myocardial Infarction", 1.34, 1.21, 1.48),
    ("Peripheral Artery Disease", 1.52, 1.36, 1.69),
    ("Pneumonia", 1.22, 1.10, 1.35),
    ("Hospitalization", 1.41, 1.27, 1.56),
    ("ICU Admission", 1.18, 1.06, 1.31),
    ("All Cause Mortality", 1.67, 1.50, 1.86),
]


FONT_CANDIDATES = [
    "Times New Roman",
    "Times",
    "Liberation Serif",
    "Nimbus Roman",
    "DejaVu Serif",
]


@dataclass(frozen=True)
class PlotStyle:
    row_pitch_pt: float = 16.0
    underline_gap_pt: float = 1.8
    underline_lw: float = 1.2
    table_font_size: int = 12
    sep_rule_w: float = 0.8
    sep_alpha: float = 0.25
    table_width_frac: float = 0.60
    fig_width_in: float = 6.6
    export_dpi: int = 600
    marker_size: int = 32
    ci_line_width: float = 1.6
    table_text_column_x: float = 0.55


@dataclass(frozen=True)
class TickConfig:
    left_xlim: float = 0.5
    right_xlim: float = 4.0
    n_left_unlabeled: int = 4
    n_right_unlabeled: int = 2
    n_right_labeled_interior: int = 0


def choose_serif_font() -> str:
    for family in FONT_CANDIDATES:
        try:
            findfont(FontProperties(family=family), fallback_to_default=False)
            return family
        except Exception:
            pass
    return "DejaVu Serif"


def coerce_plot_data(data: pd.DataFrame | Iterable[Sequence[object]]) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        df = pd.DataFrame(data, columns=["Outcome", "Mid", "Lo", "Hi"])

    rename_map = {
        "outcome": "Outcome",
        "label": "Outcome",
        "mid": "Mid",
        "mid point": "Mid",
        "midpoint": "Mid",
        "estimate": "Mid",
        "lower": "Lo",
        "lower_ci": "Lo",
        "low ci": "Lo",
        "lo": "Lo",
        "upper": "Hi",
        "upper_ci": "Hi",
        "high ci": "Hi",
        "hi": "Hi",
    }
    df = df.rename(columns={c: rename_map.get(str(c).strip().lower(), c) for c in df.columns})

    required = ["Outcome", "Mid", "Lo", "Hi"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    df = df[required].copy()
    df["Outcome"] = df["Outcome"].astype(str).str.strip()
    for col in ["Mid", "Lo", "Hi"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.replace({"Outcome": {"": np.nan}}).dropna(subset=required)
    if df.empty:
        raise ValueError("No complete rows were found. Add at least one outcome with Mid, Lo, and Hi.")

    invalid_ci = df[(df["Lo"] > df["Mid"]) | (df["Mid"] > df["Hi"])]
    if not invalid_ci.empty:
        bad_rows = ", ".join(str(i + 1) for i in invalid_ci.index.to_list()[:5])
        raise ValueError(f"Each row must satisfy Lo <= Mid <= Hi. Check row(s): {bad_rows}.")

    return df.reset_index(drop=True)


def build_ticks(config: TickConfig) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if config.left_xlim >= 1.0 or config.right_xlim <= 1.0:
        raise ValueError("Left x-limit must be below 1 and right x-limit must be above 1.")

    left_segment = np.linspace(config.left_xlim, 1.0, config.n_left_unlabeled + 2)
    right_segment = np.linspace(1.0, config.right_xlim, config.n_right_unlabeled + 2)
    all_ticks = np.concatenate((left_segment, right_segment[1:]))
    all_ticks = np.unique(np.round(all_ticks, 10))

    right_interior = [t for t in all_ticks if 1.0 < t < config.right_xlim]
    n_labeled = max(0, min(config.n_right_labeled_interior, len(right_interior)))
    label_positions = [config.left_xlim, 1.0, config.right_xlim]

    if n_labeled and right_interior:
        idxs = np.linspace(0, len(right_interior) - 1, n_labeled, dtype=int)
        label_positions.extend(right_interior[idx] for idx in np.unique(idxs))

    label_positions_arr = np.unique(np.round(label_positions, 10))
    majors, minors = [], []
    for val in all_ticks:
        if np.any(np.isclose(val, label_positions_arr, rtol=0, atol=1e-8)):
            majors.append(val)
        else:
            minors.append(val)

    return np.array(sorted(majors)), np.array(sorted(minors)), label_positions_arr


def format_tick_value(x: float) -> str:
    if abs(x - round(x)) < 1e-8:
        return str(int(round(x)))
    return f"{x:.3g}"


def make_forest_plot(
    data: pd.DataFrame | Iterable[Sequence[object]],
    effect_measure: str = "HR",
    tick_config: TickConfig | None = None,
    style: PlotStyle | None = None,
) -> plt.Figure:
    df = coerce_plot_data(data)
    tick_config = tick_config or TickConfig()
    style = style or PlotStyle()

    x_axis_label = f"{effect_measure.strip() or 'Effect'} (95% CI)"
    df[x_axis_label] = df.apply(
        lambda r: f"{r['Mid']:.2f} ({r['Lo']:.2f}-{r['Hi']:.2f})",
        axis=1,
    )

    major_ticks, minor_ticks, label_positions = build_ticks(tick_config)

    n = len(df)
    n_rows_total = n + 1
    row_pitch_in = style.row_pitch_pt / 72.0
    uline_gap_in = style.underline_gap_pt / 72.0
    text_height_in = style.table_font_size / 72.0
    fig_h_in = n_rows_total * row_pitch_in + 0.10

    fig = plt.figure(figsize=(style.fig_width_in, fig_h_in), dpi=style.export_dpi)
    gs = GridSpec(
        1,
        2,
        width_ratios=[style.table_width_frac, 1 - style.table_width_frac],
        wspace=0.06,
        left=0.06,
        right=0.98,
        top=0.98,
        bottom=0.12,
    )
    ax_tab = fig.add_subplot(gs[0, 0])
    ax_fp = fig.add_subplot(gs[0, 1])

    ax_tab.set_ylim(0, n_rows_total)
    ax_fp.set_ylim(0, n_rows_total)

    font_family = choose_serif_font()
    fp = FontProperties(family=font_family, size=style.table_font_size)

    def row_center(i: int) -> float:
        return n_rows_total - (i + 1) - 0.5

    ax_tab.axis("off")
    y_header_center = n_rows_total - 0.5
    ax_tab.text(0.02, y_header_center, "Outcome", fontproperties=fp, weight="bold", va="center", ha="left")
    ax_tab.text(
        style.table_text_column_x,
        y_header_center,
        x_axis_label,
        fontproperties=fp,
        weight="bold",
        va="center",
        ha="left",
    )

    pad_rows = (text_height_in / 2 + uline_gap_in) / row_pitch_in
    y_underline = y_header_center - pad_rows
    ax_tab.plot(
        [0.02, 0.98],
        [y_underline, y_underline],
        color="black",
        linewidth=style.underline_lw,
        solid_capstyle="butt",
        clip_on=False,
    )

    for i, row in df.iterrows():
        yc = row_center(i)
        ax_tab.text(0.02, yc, str(row["Outcome"]), fontproperties=fp, va="center", ha="left")
        ax_tab.text(
            style.table_text_column_x,
            yc,
            str(row[x_axis_label]),
            fontproperties=fp,
            va="center",
            ha="left",
        )

    light = (0, 0, 0, style.sep_alpha)
    for k in range(2, n_rows_total):
        y = n_rows_total - k
        ax_tab.plot(
            [0.02, 0.98],
            [y, y],
            color=light,
            linewidth=style.sep_rule_w,
            solid_capstyle="butt",
            clip_on=False,
        )

    ax_fp.set_xscale("linear")
    ax_fp.set_xlim(tick_config.left_xlim, tick_config.right_xlim)
    ax_fp.yaxis.set_visible(False)

    for spine in ["top", "left", "right"]:
        ax_fp.spines[spine].set_visible(False)

    ax_fp.xaxis.set_major_locator(FixedLocator(major_ticks))
    ax_fp.xaxis.set_minor_locator(FixedLocator(minor_ticks))

    def major_tick_formatter(x: float, _pos: int) -> str:
        if np.any(np.isclose(x, label_positions, rtol=0, atol=1e-8)):
            return format_tick_value(x)
        return ""

    ax_fp.xaxis.set_major_formatter(FuncFormatter(major_tick_formatter))
    ax_fp.xaxis.set_minor_formatter(NullFormatter())

    ax_fp.grid(False)
    ax_fp.axvline(1.0, linestyle=":", color="black", linewidth=1)
    ax_fp.tick_params(axis="x", which="major", length=5)
    ax_fp.tick_params(axis="x", which="minor", length=3)
    ax_fp.set_xlabel(x_axis_label, fontproperties=fp)

    ci_color = (0.30, 0.30, 0.30)
    mark_fc = (0.20, 0.36, 0.40)
    mark_ec = (0.10, 0.18, 0.20)

    for i, row in df.iterrows():
        yc = row_center(i)
        ax_fp.hlines(
            y=yc,
            xmin=row["Lo"],
            xmax=row["Hi"],
            color=ci_color,
            linewidth=style.ci_line_width,
            zorder=1,
        )
        ax_fp.scatter(
            [row["Mid"]],
            [yc],
            s=style.marker_size,
            marker="s",
            facecolor=mark_fc,
            edgecolor=mark_ec,
            linewidths=1.2,
            zorder=2,
        )

    return fig


def export_figure(fig: plt.Figure, file_format: str, dpi: int = 600) -> bytes:
    buffer = BytesIO()
    save_kwargs = {"format": file_format, "bbox_inches": "tight"}
    if file_format.lower() in {"png", "tiff", "tif"}:
        save_kwargs["dpi"] = dpi
    fig.savefig(buffer, **save_kwargs)
    buffer.seek(0)
    return buffer.getvalue()
