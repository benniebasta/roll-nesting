import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random

st.set_page_config(layout="wide")
st.title("🖨 RIP-Grade Roll Optimizer (Guillotine + Annealing)")

ROLL_WIDTH = st.sidebar.number_input("Roll Width (cm)", value=137.0)
OVERLAP = st.sidebar.number_input("Tile Overlap (cm)", value=1.0)
ITERATIONS = st.sidebar.number_input("Optimization Passes", 10, 300, 120)

# ===============================
# Panels
# ===============================
st.sidebar.header("Panels")

panel_count = st.sidebar.number_input("Number of different panel sizes", 1, 50, 5)

jobs = []
for i in range(1, panel_count + 1):
    st.sidebar.markdown(f"### Panel {i}")
    w = st.sidebar.number_input(f"W{i} (cm)", 0.0, key=f"w{i}")
    h = st.sidebar.number_input(f"H{i} (cm)", 0.0, key=f"h{i}")
    q = st.sidebar.number_input(f"Qty{i}", 0, 200, 0, key=f"q{i}")
    if w > 0 and h > 0 and q > 0:
        jobs.append((i, w, h, q))

# ===============================
# Vertical tiling
# ===============================
def tile_width_only(w, roll):
    for n in [1, 2, 3, 4, 5]:
        if w <= n * roll - (n - 1) * OVERLAP:
            return (w + (n - 1) * OVERLAP) / n, n
    return None, None

# ===============================
# Expand into tiles
# ===============================
def expand(jobs):
    pieces = []
    for pid, w, h, q in jobs:
        tile_w, n = tile_width_only(w, ROLL_WIDTH)
        if tile_w is None:
            return None
        for _ in range(q):
            for _ in range(n):
                pieces.append({
                    "pid": pid,
                    "orientations": [(tile_w, h), (h, tile_w)]
                })
    return pieces

# ===============================
# Guillotine nesting
# ===============================
def pack(pieces):
    free = [(0, 0, ROLL_WIDTH, 10000)]
    placed = []

    for p in pieces:
        best = None
        for fx, fy, fw, fh in free:
            for w, h in p["orientations"]:
                if w <= fw and h <= fh:
                    waste = fw * fh - w * h
                    if not best or waste < best[0]:
                        best = (waste, fx, fy, fw, fh, w, h)

        if not best:
            return None

        _, fx, fy, fw, fh, w, h = best
        placed.append((p["pid"], fx, fy, w, h))
        free.remove((fx, fy, fw, fh))

        r = (fx + w, fy, fw - w, h)
        b = (fx, fy + h, fw, fh - h)

        if r[2] > 0 and r[3] > 0:
            free.append(r)
        if b[2] > 0 and b[3] > 0:
            free.append(b)

    return placed

def length(placed):
    return max(y + h for _, _, y, _, h in placed)

# ===============================
# Multi-pass optimizer
# ===============================
def optimize(pieces):
    best_len = None
    best_layout = None

    for _ in range(ITERATIONS):
        random.shuffle(pieces)
        layout = pack(pieces)
        if layout:
            l = length(layout)
            if not best_len or l < best_len:
                best_len = l
                best_layout = layout

    return best_layout, best_len

# ===============================
# Run
# ===============================
if st.button("Run RIP Optimizer"):

    pieces = expand(jobs)
    if not pieces:
        st.error("Invalid panel sizes.")
        st.stop()

    best, total = optimize(pieces)

    st.success(f"RIP-Optimized Length = {total/100:.2f} meters")

    df = pd.DataFrame([(p,w,h) for p,_,_,w,h in best], columns=["Panel","Tile W","Tile H"])
    st.dataframe(df, use_container_width=True)

    fig, ax = plt.subplots(figsize=(14,8))
    colors = {}

    for pid, x, y, w, h in best:
        if pid not in colors:
            colors[pid] = (random.random(), random.random(), random.random())
        ax.add_patch(plt.Rectangle((y, x), h, w, facecolor=colors[pid], edgecolor="black"))
        ax.text(
                    y + h/2,
                    x + w/2,
                    f"{pid}\n{w:.0f}×{h:.0f}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color="black",
                    weight="bold"
                )

    ax.set_xlim(0, total)
    ax.set_ylim(0, ROLL_WIDTH)
    ax.set_xlabel("Fabric Length (cm)")
    ax.set_ylabel("Roll Width (cm)")
    ax.set_title("ONYX-Class RIP Nesting")

    st.pyplot(fig)
