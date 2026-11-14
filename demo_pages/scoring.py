"""BM25STD relevance, as a shop's results page: without ranking vs with it.

Built on Miles Song's tuned 20-product catalog. Each tab is one moment a shop
cares about, shown as two shelves side by side so the audience sees what
ranking changes for the shopper. BM25STD is a relevance feature, so the page
shows order, not latency.
"""

import streamlit as st

from demo_pages.catalog import SHOP_PRODUCTS
from demo_pages.common import (
    fmt_cmd, flatten_html, index_exists, product_grid, run, shop_header, wait_indexed,
    why_it_matters, feature_purpose,
)

INDEX = "scoring_idx"
RATED_INDEX = "scoring_rated_idx"  # same keys, with SCORE_FIELD rating
PREFIX = "score:"
SCHEMA = ["SCHEMA", "title", "TEXT", "description", "TEXT", "category", "TAG",
          "price", "NUMERIC", "SORTABLE", "sku", "NUMERIC", "SORTABLE", "rating", "NUMERIC"]
CREATE = ["FT.CREATE", INDEX, "ON", "HASH", "PREFIX", "1", PREFIX, *SCHEMA]
CREATE_RATED = ["FT.CREATE", RATED_INDEX, "ON", "HASH", "PREFIX", "1", PREFIX,
                "SCORE_FIELD", "rating", *SCHEMA]

STUFFED_SKU = 3  # "Running Shoes Sneakers Trainers - ... Best Cheap Sale"
# Review score per product, 0-1 (SCORE_FIELD multiplies BM25 by it). The
# keyword-stuffed listing is from a poorly reviewed seller; the rest are 0.6-0.95.
RATINGS = {1: 0.8, 2: 0.85, 3: 0.3, 4: 0.9, 5: 0.95, 6: 0.7, 7: 0.6}
DEFAULT_RATING = 0.8


def setup(client) -> None:
    for name in (INDEX, RATED_INDEX):
        if index_exists(client, name):
            client.execute_command("FT.DROPINDEX", name)
    for key in client.scan_iter(f"{PREFIX}*"):
        client.delete(key)
    client.execute_command(*CREATE)
    client.execute_command(*CREATE_RATED)
    for sku, (title, desc, category, price) in enumerate(SHOP_PRODUCTS, 1):
        client.hset(f"{PREFIX}{sku:02d}", mapping={
            "title": title, "description": desc, "category": category, "price": price,
            "sku": sku, "rating": RATINGS.get(sku, DEFAULT_RATING),
        })
    wait_indexed(client, INDEX, len(SHOP_PRODUCTS))
    wait_indexed(client, RATED_INDEX, len(SHOP_PRODUCTS))


def search(client, index: str, query: str, *extra) -> tuple[list, list[dict]]:
    """Run a search; return (args, rows) with each row's BM25 score."""
    args = ["FT.SEARCH", index, query, "WITHSCORES",
            "RETURN", "5", "title", "description", "category", "price", "rating",
            *extra, "LIMIT", "0", "8", "DIALECT", "2"]
    reply, _ = run(client, *args)
    rows = []
    for i in range(1, len(reply), 3):
        f = dict(zip(reply[i + 2][::2], reply[i + 2][1::2]))
        rows.append({"key": reply[i], "score": float(reply[i + 1]), **f})
    return args, rows


def tag(rows: list[dict], fn) -> list[dict]:
    """Attach a badge to the cards fn() picks out, so the audience can track them."""
    return [{**r, "badge": fn(r)} for r in rows]


def is_stuffed(r: dict) -> bool:
    return r["key"] == f"{PREFIX}{STUFFED_SKU:02d}"


def stars(r: dict) -> str:
    return f"★ {float(r.get('rating', 0)) * 5:.1f}"


def two_shelves(left_label, left_rows, right_label, right_rows, per_row=4):
    l, r = st.columns(2, gap="large")
    with l:
        st.markdown(f"**{left_label}**")
        if left_rows:
            product_grid(left_rows, per_row=min(per_row, 2), show_rank=True, badge_key="badge")
        else:
            st.markdown(flatten_html("""
                <div style="border:2px dashed #fca5a5;border-radius:14px;padding:38px 16px;
                            text-align:center;color:#b91c1c;background:#fef2f2;">
                  <div style="font-size:34px;">🫥</div>
                  <div style="font-weight:700;margin-top:6px;">0 results</div>
                  <div style="font-size:13px;">The shopper sees an empty page.</div>
                </div>"""), unsafe_allow_html=True)
    with r:
        st.markdown(f"**{right_label}**")
        product_grid(right_rows, per_row=min(per_row, 2), show_rank=True, badge_key="badge")


def behind(*cmds: tuple[str, list], note: str = "") -> None:
    with st.expander("⚙️ Behind the storefront", expanded=False):
        for label, args in cmds:
            st.markdown(f"**{label}**")
            st.code(fmt_cmd(*args), language=None)
        if note:
            st.caption(note)


def render(client) -> None:
    st.title("📊 Best match first")
    st.markdown(
        "A search box is only as good as its first row. New in 1.3, BM25STD ranks every match by how "
        "well it fits the query, and gives the shop two levers over that order: query-time boosts and "
        "a per-product score field."
    )
    feature_purpose(
        "relevance",
        "putting the right product first, and giving the shop levers over that order.",
        "the same results with and without relevance ranking. It isn't a speed demo, so "
        "there are no timings on this page.",
    )
    if not (index_exists(client, INDEX) and index_exists(client, RATED_INDEX)):
        with st.spinner("Opening the shop..."):
            setup(client)
    shop_header(f"Shoes, apparel and gear · {len(SHOP_PRODUCTS)} products")

    t1, t2, t3 = st.tabs(["🥇 Best match first", "📣 Promote a product line", "⭐ Reviews count"])

    # ---- 1. Relevance vs a sort order ----------------------------------------
    with t1:
        st.markdown("A shopper searches **running shoes**.")
        a_left, left = search(client, INDEX, "running shoes", "SORTBY", "price", "ASC")
        a_right, right = search(client, INDEX, "running shoes")
        badge = lambda r: "keyword-stuffed" if is_stuffed(r) else None
        two_shelves("Without ranking: sorted by price", tag(left, badge),
                    "With BM25STD: best match first", tag(right, badge))
        why_it_matters(
            "Without relevance, a shop falls back to price or newest, and the cheap keyword-stuffed "
            "listing wins the top spot. BM25STD caps how much repeating a word helps and discounts "
            "long, stuffed listings, so the focused product leads."
        )
        behind(("Without ranking", a_left), ("With BM25STD (no SORTBY = relevance order)", a_right),
               note="BM25STD is the default and only scorer in 1.3; `WITHSCORES` shows the scores.")

    # ---- 2. Query-time boost --------------------------------------------------
    with t2:
        st.markdown(
            "It's a rainy week. The merchandiser wants **waterproof** gear to lead every `shoes` search, "
            "without re-indexing anything."
        )
        boost = st.slider("Boost for “waterproof”", 1.0, 5.0, 3.0, 0.5)
        q_boost = f"shoes | ((waterproof) => {{$weight: {boost:g}}})"
        a_left, left = search(client, INDEX, "shoes")
        a_right, right = search(client, INDEX, q_boost)
        badge = lambda r: "waterproof" if "waterproof" in (r["title"] + r.get("description", "")).lower() else None
        two_shelves("Plain search: shoes", tag(left, badge),
                    f"Waterproof boosted × {boost:g}", tag(right, badge))
        why_it_matters(
            "`$weight` multiplies one term's contribution at query time, so merchandising is a query "
            "change rather than a data change. The boost is an OR, so waterproof gear that isn't a "
            "shoe (the rain jacket) also joins the shelf."
        )
        behind(("Plain", a_left), ("Boosted", a_right))

    # ---- 3. SCORE_FIELD ------------------------------------------------------
    with t3:
        st.markdown(
            "Same search, **shoes**, but the shop also knows each product's **review score**. "
            "`SCORE_FIELD` (new in 1.3) multiplies relevance by a per-product field."
        )
        a_left, left = search(client, INDEX, "shoes")
        a_right, right = search(client, RATED_INDEX, "shoes")
        two_shelves("Text relevance only", tag(left, stars),
                    "Relevance × review score (SCORE_FIELD rating)", tag(right, stars))
        why_it_matters(
            "Text alone can't tell a good product from a poorly reviewed one with the right words. "
            "With `SCORE_FIELD`, the badly reviewed keyword-stuffed listing (★ 1.5) drops from #4 to "
            "last, and the best-reviewed waterproof shoes rise."
        )
        behind(("Text relevance only", a_left), ("With reviews", a_right),
               ("The reviews-aware index", CREATE_RATED),
               note="`SCORE_FIELD rating` makes each key's `rating` (0–1) its document score, which "
                    "BM25STD multiplies in. A key without the field uses the index's `SCORE` "
                    "default (1.0).")
