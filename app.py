"""
Valkey Search 1.3 Demo - Streamlit Web UI

A shopping app demo showcasing valkey-search 1.3 features:
- Multi-language FTS
- BM25STD Scoring
- KNN vs Vector Range
- FT.HYBRID Search
- Cursor Pagination

Run with: streamlit run app.py
"""


import streamlit as st


# Page config must be first Streamlit command
st.set_page_config(
    page_title="Valkey Search 1.3 Demo",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Initialize session state
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "connected" not in st.session_state:
    st.session_state.connected = False
if "client" not in st.session_state:
    st.session_state.client = None


# -----------------------------------------------------------------------------
# Valkey Connection
# -----------------------------------------------------------------------------
def get_client():
    """Get or create Valkey client."""
    if st.session_state.client is None:
        try:
            from core.client import get_client as create_client
            st.session_state.client = create_client()
            st.session_state.connected = True
        except Exception as e:
            st.session_state.connected = False
            st.error(f"Failed to connect to Valkey: {e}")
            return None
    return st.session_state.client


# -----------------------------------------------------------------------------
# Feature Pages
# -----------------------------------------------------------------------------
def page_home():
    """Home page with feature overview."""
    st.title("🔍 Valkey Search 1.3 Demo")
    st.markdown("### Shopping App - Feature Showcase")
    
    st.markdown("""
    This demo showcases the new features in **valkey-search 1.3**:
    
    | Feature | What's New |
    |---------|-----------|
    | 🌍 Multi-language FTS | English rules vs `LANGUAGE`; unranked vs BM25STD |
    | 📊 BM25STD Scoring | Relevance-ranked results with WITHSCORES |
    | 📏 KNN vs Vector Range | Top-K vs everything within a radius |
    | 🔀 FT.HYBRID | Text vs vector vs fused (RRF / LINEAR / FUNCTION) |
    | 📄 Cursors | Paging with WITHCURSOR; offset vs cursor timing |
    
    👈 **Select a feature from the sidebar** to try it out!
    """)
    
    # Connection status
    client = get_client()
    if client:
        st.success("✓ Connected to Valkey")
        # Show module info
        try:
            modules = client.execute_command("MODULE", "LIST")
            for mod in modules:
                if b"search" in mod or "search" in str(mod):
                    st.caption(f"Module: {mod}")
        except:
            pass
    else:
        st.warning("⚠ Not connected to Valkey. Start the server first.")


def page_multilang():
    """Multi-language FTS: English rules vs LANGUAGE, unranked vs BM25."""
    client = get_client()
    if client:
        from demo_pages import multilang
        multilang.render(client)


def page_bm25():
    """BM25STD relevance: the same results with and without ranking."""
    client = get_client()
    if client:
        from demo_pages import scoring
        scoring.render(client)


def page_vector():
    """KNN vs VECTOR_RANGE."""
    client = get_client()
    if client:
        from demo_pages import vector_range
        vector_range.render(client)


def page_hybrid():
    """FT.HYBRID vs text vs vector."""
    client = get_client()
    if client:
        from demo_pages import hybrid
        hybrid.render(client)


def page_cursor():
    """Cursor paging storefront and offset-vs-cursor timing."""
    client = get_client()
    if client:
        from demo_pages import cursors
        cursors.render(client)


def main():
    # Sidebar navigation
    st.sidebar.title("Valkey Search 1.3")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Features",
        [
            "🏠 Home",
            "🌍 Multi-language FTS",
            "📊 BM25 Scoring",
            "📄 Cursors",
            "🔀 FT.HYBRID",
            "📏 KNN vs Vector Range",
        ]
    )
    
    # Connection status in sidebar
    st.sidebar.markdown("---")
    if st.session_state.connected:
        st.sidebar.success("✓ Connected")
    else:
        st.sidebar.warning("⚠ Disconnected")
        if st.sidebar.button("Connect"):
            get_client()
            st.rerun()
    
    # Route to page
    if page == "🏠 Home":
        page_home()
    elif page == "🌍 Multi-language FTS":
        page_multilang()
    elif page == "📊 BM25 Scoring":
        page_bm25()
    elif page == "📏 KNN vs Vector Range":
        page_vector()
    elif page == "🔀 FT.HYBRID":
        page_hybrid()
    elif page == "📄 Cursors":
        page_cursor()


if __name__ == "__main__":
    main()
