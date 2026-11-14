"""Search that understands the shopper: FT.HYBRID next to keyword-only and vector-only.

The shopper types one natural sentence into one search box. The page shows the
three shelves they could have been served, so the audience sees what keyword
search alone loses and what fusing both rankings gives back.
"""

import streamlit as st

from demo_pages.catalog import CATALOG

from demo_pages.common import (
    CAT_INDEX, DESCRIPTIONS, TITLES, catalog_detail, embed, ensure_catalog, feature_purpose, fmt_cmd,
    parse_aggregate, parse_search, rail, run, shop_header, why_it_matters,
)

# Shopper phrasings, checked against the catalog. The first word of the comment
# is what the audience should notice; re-check if the catalog changes.
PRESETS = [
    "rain jacket",                       # keyword ranks the repair-patch kit first; hybrid puts the jacket first
    "block engine noise on a plane",     # no product says "engine"; keyword search finds nothing
    "keep my coffee hot",                # keyword needs every word; hybrid still sells the mug
    "noise cancelling headphones",       # accessories crowd the keyword shelf; fusion mixes both rankings
]

# How deep each arm retrieves before fusion. The shelves show fewer; fusing deeper
# lists is what lets a product the other arm ranked lower still rise.
ARM_DEPTH = 10
RRF_CONSTANT = 60

FUSION_HELP = {
    "RRF": "Ranks by **position** in each shelf, so the two different score scales don't fight. "
           "Defaults: `CONSTANT 60`, `WINDOW 20`.",
    "LINEAR": "Weighted sum of the **raw** scores: `ALPHA × keyword + BETA × semantic`. "
              "Scores are used as they stand, so a big BM25 score can dominate — that is what "
              "`ALPHA` / `BETA` are for.",
    "FUNCTION": "Your own expression over the arm scores — a valkey-search extension. "
                "A product missing from an arm has no score there, so guard it with `exists()`.",
}


def text_args(q: str, k: int) -> list:
    return ["FT.SEARCH", CAT_INDEX, q, "RETURN", "4", "title", "description", "category", "price",
            "LIMIT", "0", str(k)]


def vector_args(v: bytes, k: int) -> list:
    return ["FT.SEARCH", CAT_INDEX, f"*=>[KNN {k} @embedding $v]", "PARAMS", "2", "v", v,
            "RETURN", "4", "title", "description", "category", "price", "DIALECT", "2"]


def hybrid_args(q: str, v: bytes, k: int, fusion: str, alpha: float, beta: float, expr: str) -> list:
    args = ["FT.HYBRID", CAT_INDEX,
            "SEARCH", q, "YIELD_SCORE_AS", "keyword_score",
            "VSIM", "@embedding", "$v", "KNN", "2", "K", str(ARM_DEPTH), "YIELD_SCORE_AS", "semantic_score"]
    if fusion == "RRF":
        args += ["COMBINE", "RRF", "2", "YIELD_SCORE_AS", "score"]
    elif fusion == "LINEAR":
        args += ["COMBINE", "LINEAR", "6", "ALPHA", str(alpha), "BETA", str(beta),
                 "YIELD_SCORE_AS", "score"]
    else:
        args += ["COMBINE", "FUNCTION", "4", "EXPR", expr, "YIELD_SCORE_AS", "score"]
    return args + ["LOAD", "4", "@__key", "@title", "@category", "@price",
                   "PARAMS", "2", "v", v, "LIMIT", "0", str(k)]


def render(client) -> None:
    st.title("🔀 Search that understands the shopper")
    st.markdown(
        "A shopper describes what they want in their own words. Keyword search only finds the words "
        "they happened to use; semantic search only finds the vibe. `FT.HYBRID` runs both over one "
        "index and fuses the two rankings in a single command."
    )
    feature_purpose(
        "relevance",
        "finding the right product when the shopper doesn't use its words, in one command instead of two searches plus merge code in the app.",
        "keyword-only, semantic-only and fused results for the same query, and the arithmetic behind the fused order. It isn't a speed demo, so there are no timings here.",
    )
    ensure_catalog(client)

    shop_header(f"Outdoor and running gear · {len(CATALOG)} products")
    with st.form("hybrid_form"):
        c1, c2 = st.columns([4, 1])
        query = c1.selectbox("Search", PRESETS, label_visibility="collapsed",
                             accept_new_options=True)
        go = c2.form_submit_button("🔍 Search", use_container_width=True)
        with st.expander("Fusion settings"):
            f1, f2, f3 = st.columns([1, 2, 2])
            fusion = f1.radio("COMBINE", ["RRF", "LINEAR", "FUNCTION"])
            alpha = f2.slider("LINEAR: ALPHA (keyword weight)", 0.0, 1.0, 0.3, 0.1)
            beta = round(1 - alpha, 1)
            f2.caption(f"BETA (semantic weight) = {beta}")
            expr = f3.text_input("FUNCTION: EXPR", value="@semantic_score + exists(@keyword_score)")
            k = f3.slider("Products per shelf", 3, 8, 4)

    if "hy_state" not in st.session_state:
        st.session_state.hy_state = (PRESETS[0], "RRF", 0.3, 0.7,
                                     "@semantic_score + exists(@keyword_score)", 4)
    if go and query.strip():
        st.session_state.hy_state = (query.strip(), fusion, alpha, beta, expr, k)
    q, fusion, alpha, beta, expr, k = st.session_state.hy_state
    v = embed(q)

    cmds = {}
    try:
        t_reply, _ = run(client, *(t_args := text_args(q, k)))
        v_reply, _ = run(client, *(v_args := vector_args(v, k)))
        h_reply, _ = run(client, *(h_args := hybrid_args(q, v, k, fusion, alpha, beta, expr)))
    except Exception as e:
        st.error(str(e))
        return
    cmds = {"keyword": t_args, "semantic": v_args, "hybrid": h_args}

    t_total, t_rows = parse_search(t_reply)
    _, v_rows = parse_search(v_reply)
    t_keys = {r["key"] for r in t_rows}
    v_keys = {r["key"] for r in v_rows}

    h_rows = []
    for rec in parse_aggregate(h_reply):
        key = rec.get("__key")
        both = key in t_keys and key in v_keys
        h_rows.append({
            "key": key,
            "title": rec.get("title") or TITLES.get(key, key),
            "description": DESCRIPTIONS.get(key, ""),
            "category": rec.get("category", ""),
            "price": rec.get("price"),
            "found": "both" if both else "keyword" if key in t_keys else "semantic",
        })

    # Each arm's ranking as fusion saw it: keyword over RRF's default WINDOW of 20,
    # semantic over the VSIM arm's K.
    kw_rank_reply, _ = run(client, "FT.SEARCH", CAT_INDEX, q, "NOCONTENT", "LIMIT", "0", "20")
    sem_rank_reply, _ = run(client, "FT.SEARCH", CAT_INDEX, f"*=>[KNN {ARM_DEPTH} @embedding $v]",
                            "PARAMS", "2", "v", v, "NOCONTENT", "DIALECT", "2")
    kw_rank = {key: i + 1 for i, key in enumerate(kw_rank_reply[1:])}
    sem_rank = {key: i + 1 for i, key in enumerate(sem_rank_reply[1:])}
    for row in h_rows:  # badge by what each arm actually retrieved, not the shorter shelves
        in_k, in_s = row["key"] in kw_rank, row["key"] in sem_rank
        row["found"] = "both" if in_k and in_s else "keyword" if in_k else "semantic"

    st.markdown(f"#### Results for “{q}”")
    rail(f"⌨️ Keyword search only — what most shops do today · {t_total} match(es)",
         t_rows, empty="Nothing matched. Every word has to appear, so the shopper sees an empty page.",
         per_row=k, note="`FT.SEARCH` over the TEXT fields, ranked by BM25STD.")
    st.divider()
    rail(f"🧠 Semantic search only · {len(v_rows)} nearest",
         v_rows, empty="No vectors returned.", per_row=k,
         note="`KNN` over the embedding. Always returns K, so the tail can drift off-topic.")
    st.divider()
    rail(f"🔀 FT.HYBRID — {fusion} fusion · {len(h_rows)} fused",
         h_rows, empty="No results.", per_row=k, badge_key="found",
         note="One command. The badge says which arm retrieved the product; `both` is what fusion rewards.")

    # One sentence on what fusion changed, computed from this query's shelves.
    t_top = t_rows[0]["title"] if t_rows else None
    v_top = v_rows[0]["title"] if v_rows else None
    h_top = h_rows[0]["title"] if h_rows else None
    if not t_rows:
        story = (f"Keyword search found **nothing** — every word has to appear. FT.HYBRID still answers, "
                 f"leading with **{h_top}** from the semantic arm.")
    elif fusion != "RRF" and h_top == t_top and t_top != v_top:
        story = (f"Under {fusion}, the keyword winner **{t_top}** stays on top: it fuses the arms' *raw* "
                 f"scores, and a BM25 score of several points swamps a vector similarity between 0 and 1. "
                 f"That is what `ALPHA` / `BETA` are for — or use RRF, which only looks at ranks.")
    elif fusion != "RRF":
        story = (f"{fusion} fuses the arms' raw scores, so **{h_top}** leads on score magnitude; switch to "
                 f"RRF to fuse by rank instead.")
    elif t_top != h_top:
        story = (f"Keyword search put **{t_top}** first. FT.HYBRID puts **{h_top}** first, because both "
                 f"arms ranked it near the top — agreement is what RRF rewards.")
    elif v_top != h_top:
        story = (f"Semantic search put **{v_top}** first. FT.HYBRID keeps the exact keyword match "
                 f"**{h_top}** on top, because both arms ranked it near the top.")
    else:
        story = (f"Both arms already agree on **{h_top}**, so it leads the fused shelf too; RRF decides "
                 f"the order of everything below it.")
    st.markdown("🧭 " + story)

    why_it_matters(
        "Shoppers rarely type exactly what the product page says. Fusing the two rankings keeps "
        "exact matches and meaning-matches on one shelf, with what both agree on at the top — "
        "and the shop runs one command instead of merging two result sets in the app."
    )

    with st.expander("🧮 How the fused order was computed", expanded=True):
        trace = []
        for i, row in enumerate(h_rows, 1):
            kr, sr = kw_rank.get(row["key"]), sem_rank.get(row["key"])
            parts = [f"1/{RRF_CONSTANT + r}" for r in (kr, sr) if r]
            score = sum(1 / (RRF_CONSTANT + r) for r in (kr, sr) if r)
            trace.append({
                "Hybrid #": i,
                "Product": row["title"],
                "Keyword rank": f"#{kr}" if kr else "—",
                "Semantic rank": f"#{sr}" if sr else "—",
                "RRF score": f"{' + '.join(parts)} = {score:.4f}" if fusion == "RRF" else "—",
            })
        st.dataframe(trace, hide_index=True, width="stretch")
        if fusion == "RRF":
            st.caption(
                f"RRF ignores the raw scores and adds `1 / ({RRF_CONSTANT} + rank)` from every arm "
                "that found the product. A product found by both arms collects two shares, so "
                "agreement beats a single high rank. Each arm retrieves deeper than the shelf — keyword "
                f"over `WINDOW 20`, semantic over `K {ARM_DEPTH}` — so a product the other arm ranked "
                "lower can still rise."
            )
        else:
            st.caption(
                "LINEAR and FUNCTION fuse the arms' raw scores instead of their ranks, so the order "
                "depends on score magnitudes; switch to RRF to see the rank arithmetic."
            )

    with st.expander("⚙️ Behind the storefront", expanded=False):
        st.markdown(f"**The one command the shop ran** — {fusion} fusion")
        st.code(fmt_cmd(*cmds["hybrid"]), language=None)
        st.markdown(FUSION_HELP[fusion])
        st.caption(
            "Each arm is scored independently — `SEARCH` by BM25STD, `VSIM` by vector distance turned "
            "into a similarity so higher is better for both — and `COMBINE` fuses the two rankings. "
            "The fused list then runs through the FT.AGGREGATE pipeline, so `LOAD`, `SORTBY`, "
            "`GROUPBY`, `LIMIT` and `WITHCURSOR` all work on it."
        )
        st.markdown("**The two shelves it replaces**")
        st.code(fmt_cmd(*cmds["keyword"]) + "\n\n" + fmt_cmd(*cmds["semantic"]), language=None)
        st.markdown("**The shop's index**")
        catalog_detail()
