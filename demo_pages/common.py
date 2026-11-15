"""Shared helpers for the comparison demo pages.

Every page shows the exact command it ran next to its results, so the audience
can map what they see back to the slides.
"""

import html
import re
import time

import numpy as np
import streamlit as st

from demo_pages.catalog import CATALOG

# -----------------------------------------------------------------------------
# Storefront rendering
# -----------------------------------------------------------------------------


def flatten_html(markup: str) -> str:
    """Collapse markup to one line and drop comments.

    st.markdown ends an HTML block at the first blank line and renders indented
    lines as a code block, so multi-line markup leaks onto the page as text.
    """
    markup = re.sub(r"<!--.*?-->", "", markup, flags=re.DOTALL)
    return "".join(line.strip() for line in markup.splitlines() if line.strip())


# Product art without any network dependency: an emoji on a tinted tile, chosen
# from words in the title so it works in every store language.
_ICONS = [
    ("👟", ("shoe", "schuh", "zapatilla", "chaussure", "basket", "sneaker", "turnschuh", "calzado", "boot")),
    ("🧦", ("sock", "socke", "calcetin", "calcetín", "chaussette")),
    ("🧥", ("jacket", "jacke", "chaqueta", "veste", "chubasquero", "rain", "regen", "impermeable", "imperméable")),
    ("🩳", ("tight", "mallas", "collant", "short")),
    ("🍶", ("bottle", "flasche", "botella", "gourde")),
    ("🎒", ("backpack", "rucksack", "mochila", "sac à dos", "sac")),
    ("⌚", ("watch", "uhr", "reloj", "montre")),
    ("🎧", ("earbud", "headphone", "kopfhörer", "auricular", "écouteur")),
    ("🔦", ("headlamp", "lamp", "lampe", "linterna", "stirnlampe", "torch")),
    ("🧘", ("yoga", "mat", "matte", "esterilla", "tapis")),
]


def product_icon(title: str, category: str = "") -> str:
    text = f"{title} {category}".lower()
    for icon, words in _ICONS:
        if any(w in text for w in words):
            return icon
    return "🛍️"


_TILE_COLORS = ["#eef2ff", "#ecfdf5", "#fef3c7", "#fee2e2", "#f3e8ff", "#e0f2fe", "#f1f5f9"]


def _tile_color(category: str) -> str:
    return _TILE_COLORS[hash(category) % len(_TILE_COLORS)] if category else _TILE_COLORS[-1]


def product_card(
    title: str,
    description: str = "",
    category: str = "",
    price=None,
    rank: int | None = None,
    badge: str | None = None,
    currency: str = "$",
) -> None:
    """One storefront product card, the way a shopper would see it."""
    esc = html.escape
    rank_chip = (
        f'<div style="position:absolute;top:8px;left:8px;background:#111827;color:#fff;border-radius:999px;'
        f'width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-size:13px;'
        f'font-weight:700;">{rank}</div>' if rank else ""
    )
    badge_chip = (
        f'<div style="position:absolute;top:8px;right:8px;background:#2563eb;color:#fff;border-radius:999px;'
        f'padding:2px 10px;font-size:11px;font-weight:600;">{esc(badge)}</div>' if badge else ""
    )
    price_line = (
        f'<div style="font-size:19px;font-weight:700;color:#111827;">{esc(currency)}{price}</div>'
        if price not in (None, "") else ""
    )
    cat_chip = (
        f'<span style="background:#f1f5f9;color:#475569;border-radius:6px;padding:2px 8px;font-size:11px;">'
        f'{esc(category)}</span>' if category else ""
    )
    desc = esc(description if len(description) <= 110 else description[:110].rstrip() + "…")
    st.markdown(flatten_html(f"""
        <div style="border:1px solid #e5e7eb;border-radius:14px;overflow:hidden;background:#fff;
                    height:300px;display:flex;flex-direction:column;">
          <div style="position:relative;background:{_tile_color(category)};height:116px;display:flex;
                      align-items:center;justify-content:center;font-size:52px;">
            {product_icon(title, category)}{rank_chip}{badge_chip}
          </div>
          <div style="padding:12px 14px;display:flex;flex-direction:column;gap:7px;flex:1;">
            <div style="font-weight:650;font-size:14.5px;line-height:1.3;color:#111827;">{esc(title)}</div>
            <div style="font-size:12px;color:#6b7280;line-height:1.4;flex:1;">{desc}</div>
            <div style="display:flex;align-items:center;justify-content:space-between;">
              {price_line}{cat_chip}
            </div>
          </div>
        </div>
    """), unsafe_allow_html=True)


def product_grid(rows: list[dict], per_row: int = 3, show_rank: bool = True,
                 badge_key: str | None = None, currency: str = "$") -> None:
    """Render search results as a storefront grid of cards."""
    for start in range(0, len(rows), per_row):
        chunk = rows[start:start + per_row]
        for col, (offset, row) in zip(st.columns(per_row), enumerate(chunk)):
            with col:
                product_card(
                    title=row.get("title", row.get("key", "")),
                    description=row.get("description", ""),
                    category=row.get("category", ""),
                    price=row.get("price"),
                    rank=start + offset + 1 if show_rank else None,
                    badge=row.get(badge_key) if badge_key else None,
                    currency=currency,
                )


# -----------------------------------------------------------------------------
# Commands
# -----------------------------------------------------------------------------


def run(client, *args):
    """Run a command; return (reply, latency_ms)."""
    start = time.perf_counter()
    reply = client.execute_command(*args)
    return reply, (time.perf_counter() - start) * 1000


def fmt_cmd(*args) -> str:
    """Render a command the way it would be typed; binary vectors show as $v."""
    out = []
    for a in args:
        if isinstance(a, bytes):
            out.append("<vector>")
        else:
            s = str(a)
            out.append(f'"{s}"' if (" " in s or s == "" or "*" in s) else s)
    return " ".join(out)


def show_cmd(*args) -> None:
    st.code(fmt_cmd(*args), language=None)


def pairs(flat) -> dict:
    return dict(zip(flat[::2], flat[1::2]))


def parse_search(reply, withscores: bool = False) -> tuple[int, list[dict]]:
    """FT.SEARCH reply -> (total, rows). Each row has 'key' (+ 'score') and its fields."""
    total, rows, step = reply[0], [], 3 if withscores else 2
    for i in range(1, len(reply), step):
        row = {"key": reply[i]}
        if withscores:
            row["score"] = round(float(reply[i + 1]), 4)
        row.update(pairs(reply[i + step - 1]) if i + step - 1 < len(reply) else {})
        rows.append(row)
    return total, rows


def parse_search_rows(rows, withscores: bool = False) -> list[dict]:
    """Rows of an FT.SEARCH cursor reply: each row is [key, (score,) [fields]]."""
    out = []
    for r in rows:
        row = {"key": r[0]}
        if withscores:
            row["score"] = round(float(r[1]), 4)
        row.update(pairs(r[-1]) if isinstance(r[-1], list) else {})
        out.append(row)
    return out


def parse_aggregate(reply) -> list[dict]:
    """FT.AGGREGATE / FT.HYBRID reply -> list of records."""
    return [pairs(rec) for rec in reply[1:]]


def form_submitted(form_key: str, clicked: bool) -> bool:
    """True once the form has been submitted, so results persist across reruns."""
    if clicked:
        st.session_state[f"{form_key}_submitted"] = True
    return st.session_state.get(f"{form_key}_submitted", False)


def index_exists(client, name: str) -> bool:
    return name in client.execute_command("FT._LIST")


def num_docs(client, name: str) -> int:
    info = client.execute_command("FT.INFO", name)
    return int(pairs(info).get("num_docs", 0))


def drop_index_and_keys(client, name: str, prefix: str) -> None:
    if index_exists(client, name):
        client.execute_command("FT.DROPINDEX", name)
    keys = list(client.scan_iter(f"{prefix}*", count=10000))
    for i in range(0, len(keys), 10000):
        client.delete(*keys[i:i + 10000])


def wait_indexed(client, name: str, expected: int, timeout_s: float = 120) -> None:
    """Wait until the index has finished backfilling `expected` documents."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if num_docs(client, name) >= expected:
            return
        time.sleep(0.2)


# -----------------------------------------------------------------------------
# Embeddings
# -----------------------------------------------------------------------------


@st.cache_resource
def get_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


def embed(text: str) -> bytes:
    """384-dim FLOAT32 embedding, as the raw bytes a HASH vector field expects."""
    return np.asarray(get_embedder().encode(text), dtype=np.float32).tobytes()


# -----------------------------------------------------------------------------
# Shared product catalog (Hybrid + Vector Range pages)
# -----------------------------------------------------------------------------

CAT_INDEX = "catalog_idx"
CAT_PREFIX = "cat:"
CAT_CREATE = [
    "FT.CREATE", CAT_INDEX, "ON", "HASH", "PREFIX", "1", CAT_PREFIX, "SCHEMA",
    "title", "TEXT", "description", "TEXT", "category", "TAG", "price", "NUMERIC",
    "embedding", "VECTOR", "HNSW", "6", "TYPE", "FLOAT32", "DIM", "384", "DISTANCE_METRIC", "COSINE",
]
TITLES = {f"{CAT_PREFIX}{sku}": title for sku, title, *_ in CATALOG}
DESCRIPTIONS = {f"{CAT_PREFIX}{sku}": desc for sku, _, desc, *_ in CATALOG}


def setup_catalog(client) -> None:
    drop_index_and_keys(client, CAT_INDEX, CAT_PREFIX)
    client.execute_command(*CAT_CREATE)
    for sku, title, desc, category, price in CATALOG:
        client.hset(f"{CAT_PREFIX}{sku}", mapping={
            "title": title, "description": desc, "category": category, "price": price,
            "embedding": embed(f"{title}. {desc}"),
        })
    wait_indexed(client, CAT_INDEX, len(CATALOG))


def ensure_catalog(client) -> bool:
    """Make sure the shop's index exists. Returns True when it is ready."""
    if not index_exists(client, CAT_INDEX):
        with st.spinner(f"Opening the shop: indexing and embedding {len(CATALOG)} products..."):
            setup_catalog(client)
    return True


def catalog_detail() -> None:
    """The shop's index and catalog, for the explainer under a storefront."""
    st.code(fmt_cmd(*CAT_CREATE), language=None)
    st.caption("Each product is embedded from `title. description` with all-MiniLM-L6-v2 (384 dims).")
    st.dataframe(
        [{"Title": t, "Description": d, "Category": c, "Price": f"${p}"} for _, t, d, c, p in CATALOG],
        hide_index=True, width="stretch",
    )


SHOP_NAME = "Trailhead Outfitters"


def shop_header(tagline: str) -> None:
    st.markdown(f"### 🏔️ {SHOP_NAME}")
    st.caption(tagline)


def feature_purpose(kind: str, purpose: str, shows: str) -> None:
    """Say up front what the feature is for and what this demo does (and doesn't) show.

    kind: "relevance", "correctness" or "performance".
    """
    icon, label, color = {
        "relevance": ("🎯", "Relevance", "#7c3aed"),
        "correctness": ("✅", "Correctness", "#059669"),
        "performance": ("⚡", "Performance", "#d97706"),
    }[kind]
    st.markdown(flatten_html(f"""
        <div style="display:flex;gap:12px;align-items:flex-start;border:1px solid #e5e7eb;
                    border-radius:10px;padding:10px 14px;margin:4px 0 14px 0;background:#fafafa;">
          <div style="background:{color};color:#fff;border-radius:999px;padding:3px 12px;
                      font-size:12px;font-weight:700;white-space:nowrap;">{icon} {label}</div>
          <div style="font-size:13.5px;color:#374151;line-height:1.45;">
            <b>What it's for:</b> {purpose}<br><b>This demo shows:</b> {shows}
          </div>
        </div>
    """), unsafe_allow_html=True)


def why_it_matters(text: str) -> None:
    """The one line that says what the shopper gets out of the feature."""
    st.markdown(flatten_html(f"""
        <div style="border-left:4px solid #2563eb;background:#eff6ff;border-radius:8px;
                    padding:10px 14px;margin:6px 0 14px 0;font-size:14px;color:#1e3a5f;">
          <b>Why this matters</b> &nbsp;{text}
        </div>
    """), unsafe_allow_html=True)


def rail(label: str, rows: list[dict], empty: str, per_row: int = 4,
         show_rank: bool = True, badge_key: str | None = None, note: str | None = None) -> None:
    """One labelled shelf of products, the way a shop lays out a result row."""
    st.markdown(f"**{label}**")
    if note:
        st.caption(note)
    if rows:
        product_grid(rows[:per_row], per_row=per_row, show_rank=show_rank, badge_key=badge_key)
    else:
        st.info(empty)
