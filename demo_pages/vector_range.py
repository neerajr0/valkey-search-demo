"""“More like this”: VECTOR_RANGE on a product page, where KNN pads and range doesn't.

A recommendation shelf is the honest test of a similarity threshold. KNN always
returns K products, so a niche item gets padded with whatever was least far away.
VECTOR_RANGE returns only what is genuinely close — sometimes nothing, which is
the right answer for a shop.
"""

import streamlit as st

from demo_pages.catalog import CATALOG
from demo_pages.common import (
    CAT_INDEX, CAT_PREFIX, catalog_detail, embed, ensure_catalog, feature_purpose, fmt_cmd,
    parse_aggregate, parse_search, product_card, rail, run, shop_header, why_it_matters,
)

PRODUCTS = {f"{CAT_PREFIX}{sku}": (title, desc, cat, price) for sku, title, desc, cat, price in CATALOG}

# Products that make the point on stage: the first has close cousins, the last
# two are one-of-a-kind, so KNN has to pad. Checked against the catalog.
FEATURED = [f"{CAT_PREFIX}{s}" for s in (1011, 1001, 1020, 1052, 1060)]


def knn_args(v: bytes, k: int) -> list:
    return ["FT.SEARCH", CAT_INDEX, f"*=>[KNN {k} @embedding $v]", "PARAMS", "2", "v", v,
            "RETURN", "5", "title", "description", "category", "price", "__embedding_score",
            "DIALECT", "2"]


def range_args(v: bytes, radius: float, limit: int = 12) -> list:
    return ["FT.SEARCH", CAT_INDEX,
            f"@embedding:[VECTOR_RANGE {radius:g} $v]=>{{$YIELD_DISTANCE_AS: similarity_distance}}",
            "PARAMS", "2", "v", v, "SORTBY", "similarity_distance",
            "RETURN", "5", "title", "description", "category", "price", "similarity_distance",
            "LIMIT", "0", str(limit), "DIALECT", "2"]


def with_match_badge(rows: list[dict], field: str, exclude: str | None = None) -> list[dict]:
    out = []
    for r in rows:
        if exclude and r["key"] == exclude:
            continue
        d = float(r[field])
        out.append({**r, "match": f"{(1 - d) * 100:.0f}% match"})
    return out


def render(client) -> None:
    st.title("📏 “More like this” that means it")
    st.markdown(
        "Recommendation shelves are where a similarity **threshold** beats a fixed count. "
        "`KNN` always returns K products; `VECTOR_RANGE` returns everything within a distance "
        "radius and nothing else."
    )
    feature_purpose(
        "correctness",
        "recommendations that only show genuinely similar products, using a similarity threshold instead of a fixed count.",
        "what lands on a \u201cmore like this\u201d shelf with KNN and with VECTOR_RANGE. It isn't a speed demo, so there are no timings here.",
    )
    ensure_catalog(client)
    shop_header("Product page · similar-items shelf")

    tab1, tab2, tab3 = st.tabs(["🛍️ Product page", "🧾 Duplicate listings", "📊 Category rollup"])

    with tab1:
        c1, c2 = st.columns([3, 2])
        key = c1.selectbox("Viewing product", FEATURED, format_func=lambda k: PRODUCTS[k][0])
        sim = c2.slider("Only show products at least this similar", 0.30, 0.90, 0.50, 0.05,
                        help="Distance radius = 1 − similarity, for a COSINE field")
        k = c2.slider("K for the KNN shelf", 3, 8, 5)
        radius = round(1 - sim, 4)

        title, desc, cat, price = PRODUCTS[key]
        hero, _ = st.columns([1, 3])
        with hero:
            product_card(title, desc, cat, price)

        v = embed(f"{title}. {desc}")
        try:
            k_reply, _ = run(client, *(k_args := knn_args(v, k + 1)))
            r_reply, _ = run(client, *(r_args := range_args(v, radius)))
        except Exception as e:
            st.error(str(e))
            return
        _, k_rows = parse_search(k_reply)
        _, r_rows = parse_search(r_reply)
        k_rows = with_match_badge(k_rows, "__embedding_score", exclude=key)[:k]
        r_rows = with_match_badge(r_rows, "similarity_distance", exclude=key)

        st.divider()
        rail(f"KNN {k} — always fills the shelf", k_rows,
             empty="No vectors returned.", per_row=min(k, 5), show_rank=False, badge_key="match",
             note="Pads with the least-far product even when nothing is really similar.")
        st.divider()
        rail(f"VECTOR_RANGE — only ≥ {sim:.0%} similar · {len(r_rows)} shown",
             r_rows, per_row=5, show_rank=False, badge_key="match",
             empty="No similar products — the shop shows no shelf instead of padding it with junk.",
             note=f"Radius {radius:g}. The count moves with the slider; KNN never does.")

        why_it_matters(
            "A shelf that can legitimately come back empty is what keeps a recommendation shelf "
            "trustworthy. Raise the slider and watch the KNN shelf keep its padding while the "
            "range shelf shrinks to only real matches."
        )

        with st.expander("⚙️ Behind the storefront", expanded=False):
            st.markdown("**The similar-items query**")
            st.code(fmt_cmd(*r_args), language=None)
            st.caption(
                "`$YIELD_DISTANCE_AS` names the distance so it can be sorted on — range results come "
                "back in key order otherwise. The radius is in the field's own metric: for `COSINE`, "
                "distance = 1 − cosine similarity, which is why the slider shows a percentage. For "
                "`L2` it is the *squared* distance. `FLAT` is exhaustive; `HNSW` is approximate and "
                "bounded by `search.max-nonvector-search-results-fetched`."
            )
            st.markdown("**What the shop would have run before 1.3**")
            st.code(fmt_cmd(*k_args), language=None)
            st.markdown("**The shop's index**")
            catalog_detail()

    with tab2:
        st.markdown(
            "A marketplace team hunting duplicate listings uses the same query: a product's own "
            "embedding, with a tight radius."
        )
        c1, c2 = st.columns([3, 2])
        dkey = c1.selectbox("Seller's listing", list(PRODUCTS), format_func=lambda k: PRODUCTS[k][0],
                            index=list(PRODUCTS).index(f"{CAT_PREFIX}1011"))
        dradius = c2.slider("Radius (distance)", 0.05, 0.50, 0.25, 0.05)
        dtitle, ddesc, *_ = PRODUCTS[dkey]
        args = range_args(embed(f"{dtitle}. {ddesc}"), dradius)
        reply, _ = run(client, *args)
        _, rows = parse_search(reply)
        rows = with_match_badge(rows, "similarity_distance", exclude=dkey)
        rail(f"Possible duplicates of “{dtitle}” · {len(rows)} found", rows,
             empty="No near-duplicates at this radius.", per_row=4, show_rank=False, badge_key="match")
        why_it_matters(
            "One query flags the same product relisted by other sellers — no K to guess at, and "
            "the radius is the policy."
        )
        with st.expander("⚙️ The query", expanded=False):
            st.code(fmt_cmd(*args), language=None)

    with tab3:
        st.markdown(
            "Because the yielded distance is a normal field, the shelf can be rolled up: the closest "
            "match per category, for a “shop by department” module."
        )
        c1, c2 = st.columns([3, 2])
        q = c1.text_input("Shopper's intent", value="gear for my morning run")
        sim3 = c2.slider("Minimum similarity", 0.10, 0.90, 0.30, 0.05, key="agg_sim")
        radius3 = round(1 - sim3, 4)
        args = ["FT.AGGREGATE", CAT_INDEX,
                f"@embedding:[VECTOR_RANGE {radius3:g} $v]=>{{$YIELD_DISTANCE_AS: dist}}",
                "PARAMS", "2", "v", embed(q),
                "LOAD", "1", "@category",
                "GROUPBY", "1", "@category", "REDUCE", "MIN", "1", "@dist", "AS", "closest",
                "REDUCE", "COUNT", "0", "AS", "products",
                "SORTBY", "2", "@closest", "ASC", "DIALECT", "2"]
        reply, _ = run(client, *args)
        recs = parse_aggregate(reply)
        st.caption(f"{len(recs)} department(s)")
        st.dataframe(
            [{"Department": r.get("category"),
              "Best match": f"{(1 - float(r['closest'])) * 100:.0f}%",
              "Products in range": r.get("products")} for r in recs] or [{"Department": "No results"}],
            hide_index=True, width="stretch",
        )
        with st.expander("⚙️ The query", expanded=False):
            st.code(fmt_cmd(*args), language=None)
