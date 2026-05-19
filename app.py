from __future__ import annotations

import pandas as pd
import streamlit as st

from forest_plotter import (
    DEFAULT_EVENT_STATS,
    PlotStyle,
    TickConfig,
    coerce_plot_data,
    export_figure,
    make_forest_plot,
)
import matplotlib.pyplot as plt


MAX_ROWS = 50


st.set_page_config(
    page_title="Forest Plotter",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    :root {
        --fp-bg: #0d1118;
        --fp-surface: #151a24;
        --fp-surface-2: #1d2330;
        --fp-border: rgba(255, 255, 255, 0.10);
        --fp-text: #f5f1e8;
        --fp-muted: #a8adba;
        --fp-accent: #e25555;
        --fp-accent-soft: rgba(226, 85, 85, 0.16);
    }

    .stApp {
        background:
            radial-gradient(circle at 18% 0%, rgba(78, 99, 125, 0.18), transparent 28rem),
            linear-gradient(180deg, #0b0f16 0%, var(--fp-bg) 34%, #0c1017 100%);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 1720px;
        padding-top: 1.25rem;
        padding-bottom: 1.25rem;
    }

    h1 {
        font-size: 2rem !important;
        line-height: 1.05 !important;
        letter-spacing: 0 !important;
        margin-bottom: 0.15rem !important;
    }

    h3 {
        font-size: 1.05rem !important;
        line-height: 1.2 !important;
        letter-spacing: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0.55rem !important;
    }

    .stCaption, [data-testid="stCaptionContainer"] {
        color: var(--fp-muted) !important;
    }

    .fp-page-title {
        text-align: center;
        margin: 0.1rem auto 1rem auto;
    }

    .fp-page-title h1 {
        font-size: 2.15rem;
        line-height: 1.05;
        letter-spacing: 0;
        margin: 0 0 0.35rem 0;
    }

    .fp-page-title p {
        color: var(--fp-muted);
        margin: 0;
        font-size: 0.95rem;
    }

    [data-testid="stMarkdownContainer"] p {
        color: inherit;
    }

    hr {
        border-color: var(--fp-border) !important;
        margin: 0.9rem 0 !important;
    }

    [data-testid="stTextInput"] label,
    [data-testid="stNumberInput"] label,
    [data-testid="stSelectbox"] label,
    [data-testid="stSlider"] label,
    [data-testid="stFileUploader"] label {
        color: var(--fp-text) !important;
        font-size: 0.82rem !important;
        font-weight: 650 !important;
    }

    .stTextInput input,
    .stNumberInput input,
    [data-baseweb="select"] > div {
        border-radius: 6px !important;
        border-color: var(--fp-border) !important;
        background: #202531 !important;
    }

    .stButton button,
    .stDownloadButton button {
        border-radius: 6px !important;
        border-color: rgba(255, 255, 255, 0.14) !important;
        background: rgba(21, 26, 36, 0.94) !important;
        color: var(--fp-text) !important;
        font-weight: 650 !important;
        min-height: 2.65rem;
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        border-color: rgba(226, 85, 85, 0.72) !important;
        background: var(--fp-accent-soft) !important;
        color: #ffffff !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        border: 1px solid var(--fp-border);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.04);
        padding: 0.55rem;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--fp-border);
        border-radius: 8px;
        overflow: hidden;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(21, 26, 36, 0.66);
        border-color: var(--fp-border);
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.14);
    }

    div[data-testid="stVerticalBlock"] {
        gap: 0.65rem;
    }

    [data-testid="stHorizontalBlock"] {
        gap: 0.9rem;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
            padding-top: 2.5rem;
        }

        h1 {
            font-size: 2rem !important;
        }

    }
    </style>
    """,
    unsafe_allow_html=True,
)


def default_data() -> pd.DataFrame:
    return pd.DataFrame(DEFAULT_EVENT_STATS, columns=["Outcome", "Mid", "Lo", "Hi"])


def load_upload(uploaded_file) -> pd.DataFrame:
    suffix = uploaded_file.name.lower().rsplit(".", 1)[-1]
    if suffix in {"xlsx", "xls"}:
        uploaded_data = pd.read_excel(uploaded_file)
    else:
        uploaded_data = pd.read_csv(uploaded_file)
    return enforce_row_limit(coerce_plot_data(uploaded_data))


def enforce_row_limit(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) > MAX_ROWS:
        raise ValueError(f"Forest Plotter supports up to {MAX_ROWS} rows at a time.")
    return df


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    renamed = df.rename(columns={"Mid": "Mid point", "Lo": "Low CI", "Hi": "High CI"})
    return renamed.to_csv(index=False).encode("utf-8")


def parse_float(text: str) -> float | None:
    try:
        return float(str(text).strip())
    except (TypeError, ValueError):
        return None


def automatic_right_minor_ticks(right_xlim: float) -> int:
    if right_xlim <= 4.25:
        return 2
    if right_xlim <= 5.25:
        return 3
    return 4


def reset_axis() -> None:
    st.session_state.left_axis_text = "0.5"
    st.session_state.right_axis_text = "4"
    st.session_state.last_valid_tick_config = TickConfig()


if "plot_data" not in st.session_state:
    st.session_state.plot_data = default_data()

if "last_valid_tick_config" not in st.session_state:
    st.session_state.last_valid_tick_config = TickConfig()

if "last_uploaded_signature" not in st.session_state:
    st.session_state.last_uploaded_signature = None


st.markdown(
    """
    <div class="fp-page-title">
        <h1>Forest Plotter</h1>
        <p>Publication-ready forest plots from pasted data, CSV, or Excel.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

top_left, top_right = st.columns([0.34, 0.66], gap="large")

with top_left:
    with st.container(border=True):
        st.subheader("Plot Controls")

        effect_col, dpi_col = st.columns(2)
        with effect_col:
            effect_measure = st.text_input("Effect measure", value="HR", help="Examples: HR, RR, OR")
        with dpi_col:
            export_dpi = st.selectbox("Raster export DPI", [300, 450, 600, 900], index=2)

        axis_inputs = st.columns(2)
        with axis_inputs[0]:
            left_xlim_text = st.text_input(
                "X-axis minimum",
                value=f"{st.session_state.last_valid_tick_config.left_xlim:g}",
                key="left_axis_text",
            )
        with axis_inputs[1]:
            right_xlim_text = st.text_input(
                "X-axis maximum",
                value=f"{st.session_state.last_valid_tick_config.right_xlim:g}",
                key="right_axis_text",
                help="This changes the right edge of the plotted x-axis and rescales the markers and CI bars.",
            )

        tick_inputs = st.columns(2)
        with tick_inputs[0]:
            n_left_unlabeled = st.number_input(
                "Left minor ticks",
                value=4,
                min_value=0,
                max_value=20,
                step=1,
                help="Adds unlabeled tick marks between the x-axis minimum and 1.",
            )
        with tick_inputs[1]:
            n_right_unlabeled = st.number_input(
                "Right minor ticks",
                value=automatic_right_minor_ticks(st.session_state.last_valid_tick_config.right_xlim),
                min_value=0,
                max_value=20,
                step=1,
                help="Adds unlabeled tick marks between 1 and the x-axis maximum. This changes tick density, not the data values.",
            )

        style_inputs = st.columns(3)
        with style_inputs[0]:
            table_width_frac = st.slider("Table width", 0.40, 0.75, 0.60, 0.01)
        with style_inputs[1]:
            table_font_size = st.slider("Font size", 8, 18, 11, 1)
        with style_inputs[2]:
            marker_size = st.slider("Marker", 12, 90, 28, 2)

        size_inputs = st.columns(3)
        with size_inputs[0]:
            fig_width_in = st.slider("Figure width", 5.5, 13.0, 6.8, 0.1)
        with size_inputs[1]:
            row_pitch_pt = st.slider("Row spacing", 11.0, 26.0, 14.0, 0.5)
        with size_inputs[2]:
            st.button("Reset axis", on_click=reset_axis, width="stretch")

with top_right:
    preview_slot = st.container()

left_xlim = parse_float(left_xlim_text)
right_xlim = parse_float(right_xlim_text)
axis_warning = None

if left_xlim is None or right_xlim is None:
    tick_config = st.session_state.last_valid_tick_config
    axis_warning = "Enter numeric x-axis limits. The preview is using the last valid axis settings."
elif left_xlim <= 0 or right_xlim <= 0:
    tick_config = st.session_state.last_valid_tick_config
    axis_warning = "X-axis limits must be positive. The preview is using the last valid axis settings."
elif left_xlim >= right_xlim:
    tick_config = st.session_state.last_valid_tick_config
    axis_warning = "The left x-axis limit must be smaller than the right limit. The preview is using the last valid axis settings."
elif not left_xlim < 1.0 < right_xlim:
    tick_config = st.session_state.last_valid_tick_config
    axis_warning = "The x-axis must keep 1 between the left and right limits. The preview is using the last valid axis settings."
else:
    tick_config = TickConfig(
        left_xlim=float(left_xlim),
        right_xlim=float(right_xlim),
        n_left_unlabeled=int(n_left_unlabeled),
        n_right_unlabeled=int(n_right_unlabeled),
        n_right_labeled_interior=0,
    )
    st.session_state.last_valid_tick_config = tick_config

if axis_warning:
    with top_left:
        st.warning(axis_warning)

style = PlotStyle(
    row_pitch_pt=float(row_pitch_pt),
    table_font_size=int(table_font_size),
    table_width_frac=float(table_width_frac),
    fig_width_in=float(fig_width_in),
    export_dpi=int(export_dpi),
    marker_size=int(marker_size),
) 

st.divider()
data_title_col, data_upload_col, data_actions_col = st.columns([0.18, 0.34, 0.48], gap="medium")
with data_title_col:
    st.subheader("Data")
with data_upload_col:
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"], label_visibility="collapsed")
with data_actions_col:
    actions = st.columns(3)
    with actions[0]:
        if st.button("Load example", width="stretch"):
            example_df = default_data()
            st.session_state.plot_data = example_df
            st.rerun()
    with actions[1]:
        st.download_button(
            "CSV template",
            data=to_csv_bytes(default_data()),
            file_name="forest_plot_template.csv",
            mime="text/csv",
            width="stretch",
        )
    with actions[2]:
        if st.button("Add row", width="stretch"):
            if len(st.session_state.plot_data) >= MAX_ROWS:
                st.warning(f"Forest Plotter supports up to {MAX_ROWS} rows at a time.")
            else:
                updated_df = pd.concat(
                    [
                        st.session_state.plot_data,
                        pd.DataFrame([{"Outcome": "", "Mid": None, "Lo": None, "Hi": None}]),
                    ],
                    ignore_index=True,
                )
                st.session_state.plot_data = updated_df
                st.rerun()

if uploaded_file is not None:
    uploaded_signature = (uploaded_file.name, uploaded_file.size)
    try:
        if uploaded_signature != st.session_state.last_uploaded_signature:
            uploaded_df = load_upload(uploaded_file)
            st.session_state.plot_data = uploaded_df
            st.session_state.last_uploaded_signature = uploaded_signature
            st.rerun()
    except Exception as exc:
        st.error(f"Could not read uploaded file: {exc}")

edited_data = st.data_editor(
    st.session_state.plot_data,
    num_rows="dynamic",
    width="stretch",
    height=170,
    column_config={
        "Outcome": st.column_config.TextColumn("Outcome", width="large", required=True),
        "Mid": st.column_config.NumberColumn("Mid point", min_value=0.0, format="%.3f", required=True),
        "Lo": st.column_config.NumberColumn("Low CI", min_value=0.0, format="%.3f", required=True),
        "Hi": st.column_config.NumberColumn("High CI", min_value=0.0, format="%.3f", required=True),
    },
    hide_index=True,
)
try:
    st.session_state.plot_data = enforce_row_limit(edited_data)
except ValueError as exc:
    st.error(str(exc))

with preview_slot:
    try:
        clean_data = enforce_row_limit(coerce_plot_data(st.session_state.plot_data))
        fig = make_forest_plot(
            clean_data,
            effect_measure=effect_measure,
            tick_config=tick_config,
            style=style,
        )
        with st.container(border=True):
            st.subheader("Preview")
            st.pyplot(fig, clear_figure=False, width="stretch")

            pdf_bytes = export_figure(fig, "pdf", dpi=export_dpi)
            png_bytes = export_figure(fig, "png", dpi=export_dpi)
            tiff_bytes = export_figure(fig, "tiff", dpi=export_dpi)
            plt.close(fig)

            downloads = st.columns(3)
            with downloads[0]:
                st.download_button(
                    "PDF",
                    data=pdf_bytes,
                    file_name="forestpanel.pdf",
                    mime="application/pdf",
                    width="stretch",
                )
            with downloads[1]:
                st.download_button(
                    "PNG",
                    data=png_bytes,
                    file_name="forestpanel.png",
                    mime="image/png",
                    width="stretch",
                )
            with downloads[2]:
                st.download_button(
                    "TIFF",
                    data=tiff_bytes,
                    file_name="forestpanel.tiff",
                    mime="image/tiff",
                    width="stretch",
                )

    except Exception as exc:
        st.error(str(exc))
        st.info("Check that every row has an outcome, midpoint, lower CI, and upper CI.")
