"""Cursor paging: a storefront that pages with WITHCURSOR, and offset vs cursor timing."""

import random
import time

import streamlit as st

from demo_pages.common import (
    drop_index_and_keys, fmt_cmd, index_exists, num_docs, parse_search, parse_search_rows,
    feature_purpose, product_grid, run, shop_header, wait_indexed, why_it_matters,
)

BULK_INDEX = "bulk_idx"
BULK_PREFIX = "bulk:"
BULK_CREATE = ["FT.CREATE", BULK_INDEX, "ON", "HASH", "PREFIX", "1", BULK_PREFIX, "SCHEMA",
               "title", "TEXT", "category", "TAG", "price", "NUMERIC"]

_ADJ = ["lightweight", "waterproof", "breathable", "insulated", "durable", "compact", "classic", "premium",
        "eco", "padded", "reflective", "ultralight", "thermal", "foldable", "rugged", "vintage"]
_ITEMS = {
    "shoes": ["running shoes", "trail shoes", "hiking boots", "sneakers", "sandals", "loafers"],
    "apparel": ["rain jacket", "running shorts", "base layer", "hoodie", "socks", "beanie"],
    "outdoor": ["backpack", "tent", "sleeping bag", "headlamp", "camp stove", "trekking poles"],
    "kitchen": ["water bottle", "travel mug", "lunch box", "coffee grinder", "kettle", "cutting board"],
}
_BRANDS = ["Northpeak", "Riverstone", "Altura", "Summitry", "Bluefjord", "Kestrel", "Oakline", "Tidewater"]


def gen_product(i: int, rnd: random.Random) -> dict:
    category = rnd.choice(list(_ITEMS))
    item = rnd.choice(_ITEMS[category])
    title = f"{rnd.choice(_BRANDS)} {rnd.choice(_ADJ)} {item} #{i}"
    return {"title": title, "category": category, "price": rnd.randint(9, 399)}


def setup_bulk(client, n: int) -> None:
    drop_index_and_keys(client, BULK_INDEX, BULK_PREFIX)
    client.execute_command(*BULK_CREATE)
    rnd = random.Random(13)  # deterministic catalog
    pipe = client.pipeline(transaction=False)
    for i in range(n):
        pipe.hset(f"{BULK_PREFIX}{i}", mapping=gen_product(i, rnd))
        if i % 5000 == 4999:
            pipe.execute()
    pipe.execute()
    wait_indexed(client, BULK_INDEX, n, timeout_s=600)


# -----------------------------------------------------------------------------
# Storefront: page through results with a server-side cursor
# -----------------------------------------------------------------------------

def _cursor_state() -> dict:
    return st.session_state.setdefault("cursor_store", {})


def _read_page(client, cursor_id: int, page: int) -> tuple[list[dict], int, float]:
    reply, ms = run(client, "FT.CURSOR", "READ", BULK_INDEX, cursor_id, "COUNT", page)
    rows_block, next_id = reply[0], reply[1]
    return parse_search_rows(rows_block[1:]), int(next_id), ms


def storefront(client) -> None:
    """A category page the shopper keeps scrolling: each 'Load more' is a cursor read."""
    s = _cursor_state()
    shop_header("Category page · browse a 100,000-product catalog")
    with st.form("store_form"):
        c1, c2, c3 = st.columns([3, 1, 1])
        q = c1.text_input("Search the store", value="waterproof", label_visibility="collapsed",
                          placeholder="Search the store")
        page = c2.select_slider("Products per batch", [6, 12, 24], value=12)
        go = c3.form_submit_button("🔍 Search", use_container_width=True)

    if go or not s.get("batches"):
        if s.get("next_id"):  # release the previous search's cursor
            try:
                client.execute_command("FT.CURSOR", "DEL", BULK_INDEX, s["next_id"])
            except Exception:
                pass
        args = ["FT.SEARCH", BULK_INDEX, q, "RETURN", "3", "title", "category", "price",
                "LIMIT", "0", 1000, "WITHCURSOR", "COUNT", page]
        reply, ms = run(client, *args)
        s.clear()
        s.update(cmd=fmt_cmd(*args), query=q, total=reply[0], batches=[parse_search_rows(reply[1])],
                 batch_ms=[ms], next_id=int(reply[2]), page_size=page, prefetched=None)

    # Prefetch the next batch so "Load more" lands instantly, the way a real
    # storefront hides latency behind a scroll.
    if s["next_id"] and s["prefetched"] is None:
        try:
            s["prefetched"] = _read_page(client, s["next_id"], s["page_size"])
        except Exception as e:  # e.g. the cursor idled past MAXIDLE and was destroyed
            st.warning(f"Cursor no longer available ({e}). Cursors expire after MAXIDLE "
                       "(default 300000 ms) without a read; search again.")
            s["next_id"], s["prefetched"] = 0, ([], 0, 0.0)

    shown = [row for batch in s["batches"] for row in batch]
    st.markdown(f"**{s['total']:,} products** match “{s['query']}” · showing {len(shown)}")
    product_grid(shown, per_row=4, show_rank=False)

    more = bool(s["next_id"] and s["prefetched"] and s["prefetched"][0])
    c1, c2 = st.columns([1, 3])
    if more:
        if c1.button("⬇️ Load more", use_container_width=True, type="primary"):
            rows, nid, ms = s["prefetched"]
            s["batches"].append(rows)
            s["batch_ms"].append(ms)
            s["next_id"], s["prefetched"] = nid, None
            st.rerun()
        c2.caption(
            f"Batch {len(s['batches'])} arrived in **{s['batch_ms'][-1]:.2f} ms** · "
            f"cursor `{s['next_id']}` is holding the rest server-side"
        )
    else:
        c2.caption("End of results — the cursor returned id 0 and the server already freed it.")

    why_it_matters(
        "The shopper keeps scrolling and every batch lands in a fraction of a millisecond, because "
        "the search ran once. Offset paging would re-run it for every batch — the tab next door "
        "measures both."
    )

    with st.expander("⚙️ Behind the storefront", expanded=False):
        st.markdown("**The first batch — one search, cursor left open**")
        st.code(s["cmd"], language=None)
        st.markdown("**Every “Load more” after that**")
        st.code(f"FT.CURSOR READ {BULK_INDEX} {s['next_id'] or '<cursor_id>'} "
                f"COUNT {s['page_size']}", language=None)
        st.caption(
            "A cursor is a snapshot of the query output, so products added while the shopper scrolls "
            "don't shuffle the batches underneath them. Rows are freed as they are read, the cursor "
            "expires after `MAXIDLE` (default 300000 ms) if the shopper walks away, and "
            "`FT.CURSOR DEL` releases it early. In a cluster the cursor lives on the node that ran "
            "the query."
        )
        st.markdown("**The catalog**")
        st.code(fmt_cmd(*BULK_CREATE), language=None)
        st.dataframe(shown[:12], hide_index=True, width="stretch")


# -----------------------------------------------------------------------------
# Offset paging vs cursor paging
# -----------------------------------------------------------------------------

def compare(client, q: str, page: int, pages: int) -> tuple[list[float], list[float], list[list[str]], list[list[str]]]:
    """Page through the same results both ways; return per-page latencies and keys."""
    offset_ms, offset_keys = [], []
    for p in range(pages):
        reply, ms = run(client, "FT.SEARCH", BULK_INDEX, q, "RETURN", "1", "title",
                        "LIMIT", p * page, page)
        offset_ms.append(ms)
        offset_keys.append(parse_search(reply)[1])

    cursor_ms, cursor_keys = [], []
    reply, ms = run(client, "FT.SEARCH", BULK_INDEX, q, "RETURN", "1", "title",
                    "LIMIT", "0", pages * page, "WITHCURSOR", "COUNT", page)
    cursor_ms.append(ms)
    cursor_keys.append(parse_search_rows(reply[1]))
    cid = int(reply[2])
    while cid and len(cursor_ms) < pages:
        rows, cid, ms = _read_page(client, cid, page)
        cursor_ms.append(ms)
        cursor_keys.append(rows)
    if cid:
        client.execute_command("FT.CURSOR", "DEL", BULK_INDEX, cid)
    return offset_ms, cursor_ms, offset_keys, cursor_keys


def benchmark(client) -> None:
    st.markdown(
        "**Offset paging** re-runs the search for every page (`LIMIT offset count`). "
        "**Cursor paging** runs it once and reads each next page from the server-side result."
    )
    with st.form("bench_form"):
        c1, c2, c3 = st.columns([2, 1, 1])
        q = c1.text_input("Query", value="running shoes")
        page = c2.select_slider("Page size", [10, 20, 50, 100], value=20)
        pages = c3.select_slider("Pages", [10, 25, 50, 100], value=50)
        go = st.form_submit_button("Page through both ways", type="primary")
    if not go:
        return
    with st.spinner("Paging..."):
        off, cur, off_rows, cur_rows = compare(client, q, page, pages)

    c1, c2, c3 = st.columns(3)
    c1.metric("Offset paging: total", f"{sum(off):.1f} ms", f"{len(off)} searches", delta_color="off")
    c2.metric("Cursor paging: total", f"{sum(cur):.1f} ms", f"1 search + {len(cur) - 1} reads", delta_color="off")
    if sum(cur) > 0:
        c3.metric("Speed-up", f"{sum(off) / sum(cur):.1f}×")
    n = min(len(off), len(cur))
    st.line_chart({"offset paging (ms)": off[:n], "cursor paging (ms)": cur[:n]},
                  x_label="page", y_label="latency per page (ms)")
    same = all({r["key"] for r in a} == {r["key"] for r in b} for a, b in zip(off_rows, cur_rows))
    st.caption(
        f"Page 1 of cursor paging includes running the search once. "
        f"Pages returned the same products both ways: {'yes' if same else 'no'}. "
        f"Latencies are client round-trips measured live from this app."
    )
    with st.expander("Commands"):
        st.code(f"# offset paging, page p\nFT.SEARCH {BULK_INDEX} \"{q}\" RETURN 1 title LIMIT <p*{page}> {page}\n\n"
                f"# cursor paging\nFT.SEARCH {BULK_INDEX} \"{q}\" RETURN 1 title LIMIT 0 {pages * page} "
                f"WITHCURSOR COUNT {page}\nFT.CURSOR READ {BULK_INDEX} <cursor_id> COUNT {page}", language=None)


def render(client) -> None:
    st.title("📄 Browsing a huge catalog")
    st.markdown(
        "A shopper scrolling a category page is the everyday case for cursors: run the search once, "
        "then hand out the rest of the results batch by batch as they scroll."
    )
    feature_purpose(
        "performance",
        "paging through a big result set without re-running the search for every page; "
        "also a functional win, since the pages are a consistent snapshot.",
        "batches read from an open cursor, and a live measurement of offset paging against cursor "
        "paging over the same results. This is the page where the timings are the point.",
    )

    exists = index_exists(client, BULK_INDEX)
    with st.expander(f"Catalog: generated products in `{BULK_INDEX}`"
                     + (f" ({num_docs(client, BULK_INDEX):,} indexed)" if exists else "")):
        st.code(fmt_cmd(*BULK_CREATE), language=None)
        n = st.select_slider("Products", [10_000, 50_000, 100_000, 200_000], value=100_000)
        load = st.button("Generate & load")
    if load or not exists:
        with st.spinner(f"Loading {n:,} products..."):
            t = time.time()
            setup_bulk(client, n)
        st.success(f"Loaded {n:,} products in {time.time() - t:.1f}s")

    tab1, tab2 = st.tabs(["🛍️ Browse the category", "⚡ Offset vs cursor"])
    with tab1:
        storefront(client)
    with tab2:
        benchmark(client)
