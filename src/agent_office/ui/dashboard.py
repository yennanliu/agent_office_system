import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import streamlit as st

from agent_office.db.database import RunStatus, get_all_runs, init_db

st.set_page_config(page_title="Agent Office", page_icon="🤖", layout="wide")
st.title("🤖 Agent Office — Run Dashboard")

init_db()


@st.cache_data(ttl=30)
def _load_runs():
    return get_all_runs()


# ── Controls ──────────────────────────────────────────────────────────────────
col_refresh, col_filter = st.columns([1, 3])
with col_refresh:
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# ── Load data ─────────────────────────────────────────────────────────────────
runs = _load_runs()

if not runs:
    st.info("No runs recorded yet. Run a command to see results here.")
    st.stop()

df = pd.DataFrame(runs)

# ── Summary metrics ───────────────────────────────────────────────────────────
status_counts = df["status"].value_counts()
total = len(df)
success = status_counts.get(RunStatus.SUCCESS, 0)
failed = status_counts.get(RunStatus.FAILED, 0)
running = status_counts.get(RunStatus.RUNNING, 0)
total_tokens = int(df["total_tokens"].sum())
total_cost = df["estimated_cost_usd"].sum()

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Runs", total)
c2.metric("✅ Success", success)
c3.metric("❌ Failed", failed)
c4.metric("⏳ Running", running)
c5.metric("Total Tokens", f"{total_tokens:,}")
c6.metric("Est. Cost (USD)", f"${total_cost:.4f}")

st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────
with col_filter:
    job_types = ["All"] + sorted(df["job_type"].dropna().unique().tolist())
    selected_type = st.selectbox("Filter by job type", job_types)

statuses = ["All", RunStatus.SUCCESS, RunStatus.FAILED, RunStatus.RUNNING]
selected_status = st.selectbox("Filter by status", statuses)

filtered = df
if selected_type != "All":
    filtered = filtered[filtered["job_type"] == selected_type]
if selected_status != "All":
    filtered = filtered[filtered["status"] == selected_status]

# ── Runs table ────────────────────────────────────────────────────────────────
st.subheader(f"Runs ({len(filtered)})")

display_cols = [
    "id", "name", "job_type", "agents", "status",
    "started_at", "finished_at",
    "total_tokens", "prompt_tokens", "completion_tokens", "estimated_cost_usd",
    "error",
]
display_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[display_cols].rename(columns={"estimated_cost_usd": "cost_usd"}),
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.NumberColumn("ID", width="small"),
        "status": st.column_config.TextColumn("Status", width="small"),
        "total_tokens": st.column_config.NumberColumn("Tokens", format="%d"),
        "cost_usd": st.column_config.NumberColumn("Cost (USD)", format="$%.4f"),
    },
)

# ── Charts ────────────────────────────────────────────────────────────────────
st.divider()
chart_df = df[df["total_tokens"] > 0].copy()
if not chart_df.empty:
    chart_df["started_at"] = pd.to_datetime(chart_df["started_at"])
    chart_df = chart_df.sort_values("started_at")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Token Usage per Run")
        st.bar_chart(chart_df.set_index("started_at")["total_tokens"])

    with col_b:
        st.subheader("Runs by Job Type")
        type_counts = df["job_type"].value_counts().reset_index()
        type_counts.columns = ["job_type", "count"]
        st.bar_chart(type_counts.set_index("job_type")["count"])
