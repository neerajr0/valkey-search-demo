"""A localized shopping site: each store serves its own language, end to end.

One `store:` prefix holds every product; each language gets its own index via
`FILTER '@lang == "<language>"'` plus `LANGUAGE`, which is the pattern on the
Multi-language usage slide. Shoppers type natural queries in their own language
and the storefront answers in it.
"""

import streamlit as st

from demo_pages.catalog import STORE
from demo_pages.common import (
    drop_index_and_keys, feature_purpose, fmt_cmd, index_exists, product_grid, run, wait_indexed,
)

PREFIX = "store:"

# Localized storefront chrome, so the whole page is in the store's language.
UI = {
    "english": dict(flag="🇬🇧 English", shop="Trailhead Outfitters", placeholder="Search products",
                    button="Search", results="{n} products", results_one="1 product", none="No products matched.",
                    sort="Sort by", relevance="Relevance", price="Price: low to high",
                    newest="Newest arrivals", currency="$",
                    examples=["waterproof jackets", "running shoes", "blisters", "cold drinks",
                              "running in the dark"]),
    "german": dict(flag="🇩🇪 Deutsch", shop="Trailhead Ausstatter", placeholder="Produkte suchen",
                   button="Suchen", results="{n} Produkte", results_one="1 Produkt", none="Keine Produkte gefunden.",
                   sort="Sortieren nach", relevance="Relevanz", price="Preis: aufsteigend",
                   newest="Neuheiten", currency="€",
                   examples=["wasserdichte Jacken", "Jacken für Kinder", "Laufschuhe",
                             "Socken gegen Blasen", "Kopfhörer zum Laufen", "laufen im Winter",
                             "Flaschen", "Lampen"]),
    "spanish": dict(flag="🇪🇸 Español", shop="Trailhead Equipamiento", placeholder="Buscar productos",
                    button="Buscar", results="{n} productos", results_one="1 producto", none="No se encontraron productos.",
                    sort="Ordenar por", relevance="Relevancia", price="Precio: de menor a mayor",
                    newest="Novedades", currency="€",
                    examples=["chaquetas impermeables", "zapatillas para correr", "¿Llueve?",
                              "calcetines", "correr en invierno", "mochilas", "botellas",
                              "linternas"]),
    "french": dict(flag="🇫🇷 Français", shop="Trailhead Équipement", placeholder="Rechercher des produits",
                   button="Rechercher", results="{n} produits", results_one="1 produit", none="Aucun produit trouvé.",
                   sort="Trier par", relevance="Pertinence", price="Prix croissant",
                   newest="Nouveautés", currency="€",
                   examples=["vestes imperméables", "chaussure de course", "chaussettes",
                             "courir en hiver", "gourdes", "lampes", "écouteurs", "randonnée"]),
}


def index_name(lang: str) -> str:
    return f"store_{lang}"


def create_args(lang: str) -> list:
    return ["FT.CREATE", index_name(lang), "ON", "HASH", "PREFIX", "1", PREFIX,
            "FILTER", f'@lang == "{lang}"', "LANGUAGE", lang, "SCHEMA",
            "title", "TEXT", "description", "TEXT", "category", "TAG",
            "price", "NUMERIC", "SORTABLE", "sku", "NUMERIC", "SORTABLE", "lang", "TAG"]


def setup(client) -> None:
    for lang in STORE:
        if index_exists(client, index_name(lang)):
            client.execute_command("FT.DROPINDEX", index_name(lang))
    drop_index_and_keys(client, index_name(next(iter(STORE))), PREFIX)
    for lang, products in STORE.items():
        client.execute_command(*create_args(lang))
        for sku, title, desc, category, price in products:
            client.hset(f"{PREFIX}{lang}:{sku}", mapping={
                "sku": sku, "title": title, "description": desc,
                "category": category, "price": price, "lang": lang,
            })
    for lang, products in STORE.items():
        wait_indexed(client, index_name(lang), len(products))


def ready(client) -> bool:
    return all(index_exists(client, index_name(lang)) for lang in STORE)


SORTS = {
    "relevance": [],                                  # BM25STD order, the default
    "price": ["SORTBY", "price", "ASC"],
    "newest": ["SORTBY", "sku", "DESC"],
}


def render(client) -> None:
    st.title("🌍 A shop in your language")
    st.markdown(
        "One catalog, one `store:` key prefix, one index per language. Switch the store and "
        "the whole shop — products, categories and search — speaks that language."
    )

    feature_purpose(
        "correctness",
        "matching the way each language actually works: plurals and inflections, stop words, "
        "and language-specific punctuation.",
        "the same shop in four languages answering natural queries in each. It isn't a speed demo, "
        "so there are no timings here.",
    )

    langs = list(STORE)
    lang = st.radio("Store", langs, format_func=lambda l: UI[l]["flag"], horizontal=True)
    ui = UI[lang]
    idx = index_name(lang)

    if not ready(client):
        with st.spinner("Building the localized storefront..."):
            setup(client)

    # ---- storefront -------------------------------------------------------
    st.markdown(f"### 🏔️ {ui['shop']}")
    with st.form(f"store_{lang}"):
        c1, c2, c3 = st.columns([3, 2, 1])
        query = c1.text_input(ui["placeholder"], value=ui["examples"][0],
                              label_visibility="collapsed", placeholder=ui["placeholder"])
        sort = c2.selectbox(ui["sort"], list(SORTS),
                            format_func=lambda s: ui[s if s != "relevance" else "relevance"],
                            label_visibility="collapsed")
        go = c3.form_submit_button(f"🔍 {ui['button']}", use_container_width=True)

    st.caption("Try: " + " · ".join(f"`{e}`" for e in ui["examples"]))

    if f"ml_q_{lang}" not in st.session_state:
        st.session_state[f"ml_q_{lang}"] = (ui["examples"][0], "relevance")
    if go and query.strip():
        st.session_state[f"ml_q_{lang}"] = (query.strip(), sort)
    q, sort = st.session_state[f"ml_q_{lang}"]

    args = ["FT.SEARCH", idx, q, "RETURN", "4", "title", "description", "category", "price",
            *SORTS[sort], "LIMIT", "0", "9", "DIALECT", "2"]
    try:
        reply, _ = run(client, *args)
    except Exception as e:
        st.error(str(e))
        return

    total = reply[0]
    rows = [dict(zip(reply[i + 1][::2], reply[i + 1][1::2])) for i in range(1, len(reply), 2)]
    label = ui["results_one"] if total == 1 else ui["results"].format(n=total)
    st.markdown(f"**{label}**")
    if rows:
        product_grid(rows, per_row=3, show_rank=(sort == "relevance"), currency=ui["currency"])
    else:
        st.info(ui["none"])

    # ---- what the shop actually ran --------------------------------------
    with st.expander("⚙️ Behind the storefront", expanded=False):
        st.markdown(f"**The shopper's search** — `{q}`, sorted by *{ui[sort]}*")
        st.code(fmt_cmd(*args), language=None)
        if sort == "relevance":
            st.caption(
                "No `SORTBY`, so the order is the BM25STD relevance ranking — the numbered badges "
                "on the cards. The other sort options replace it with `SORTBY price` / `SORTBY sku`."
            )
        st.markdown(f"**This store's index** — only `{lang}` products, tokenized and stemmed for `{lang}`")
        st.code(fmt_cmd(*create_args(lang)), language=None)
        st.caption(
            f"Every product shares the `{PREFIX}` prefix. `FILTER '@lang == \"{lang}\"'` keeps this index "
            f"to one language, and `LANGUAGE {lang}` gives it that language's stemmer, stop words and "
            "punctuation — so plurals, inflections and `¿…?` all behave the way a local shopper expects."
        )
        st.markdown("**The same shop, all four languages**")
        st.dataframe(
            [{"Store": UI[l]["flag"], "Index": index_name(l), "Products": len(STORE[l]),
              "Example query": UI[l]["examples"][0]} for l in langs],
            hide_index=True, width="stretch",
        )
