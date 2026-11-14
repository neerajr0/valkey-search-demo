# Valkey Search 1.3 Demo - Shopping App

A multi-language product search demo showcasing Valkey Search 1.3 features through a realistic e-commerce use case. Includes both a Streamlit web UI and an interactive CLI.

## Features Demonstrated

Each page of the web UI is one part of a shop, with the shopper's view on top and the exact
command underneath. Every page opens with what the feature is for, and only the Cursors page
shows timings, because it is the only performance feature.

| Page | Feature | What it shows | Module | PR |
|------|---------|---------------|--------|-----|
| 🌍 Multi-language FTS | Correctness | One shop in English, German, Spanish and French; natural queries in each | `demo_pages/multilang.py` | [#1263](https://github.com/valkey-io/valkey-search/pull/1263) |
| 📊 BM25 Scoring | Relevance | Without vs with ranking; `$weight` boosts; `SCORE_FIELD` review scores | `demo_pages/scoring.py` | [#1287](https://github.com/valkey-io/valkey-search/pull/1287) |
| 📄 Cursors | Performance | "Load more" from a cursor; offset vs cursor paging, measured live | `demo_pages/cursors.py` | [#1394](https://github.com/valkey-io/valkey-search/pull/1394) |
| 🔀 FT.HYBRID | Relevance | Keyword vs semantic vs fused shelves, with the RRF arithmetic | `demo_pages/hybrid.py` | [#1083](https://github.com/valkey-io/valkey-search/pull/1083) |
| 📏 KNN vs Vector Range | Correctness | A "more like this" shelf: KNN pads, VECTOR_RANGE shows only real matches | `demo_pages/vector_range.py` | [#985](https://github.com/valkey-io/valkey-search/pull/985) |

The interactive CLI (`demo/cli.py`) still uses the older `features/` modules.

## Prerequisites

- Docker
- A `libsearch.so` built from the [valkey-search](https://github.com/valkey-io/valkey-search) `1.3` branch (see [Building libsearch.so](#building-libsearchso) below)

## Quick Start (Docker)

### 1. Build `libsearch.so` and place it in this directory

See [Building libsearch.so](#building-libsearchso) for instructions. The file should be at `./libsearch.so`.

### 2. Start everything

```bash
# If you have docker compose (v2 plugin):
docker compose up -d

# If not, start containers manually:
docker network create valkey-demo-net

# Valkey server with search module
docker run -d \
  --name valkey-search-demo \
  --network valkey-demo-net \
  -v ./libsearch.so:/usr/lib/valkey/modules/libsearch.so:ro \
  valkey/valkey:unstable \
  valkey-server \
    --loadmodule /usr/lib/valkey/modules/libsearch.so \
    --save "" --appendonly no

# Streamlit app
docker build -t valkey-search-demo-app .
docker run -d \
  --name valkey-search-demo-app \
  --network valkey-demo-net \
  -p 127.0.0.1:8501:8501 \
  -e VALKEY_HOST=valkey-search-demo \
  -e VALKEY_PORT=6379 \
  valkey-search-demo-app
```

### 3. Open the app

Open [http://localhost:8501](http://localhost:8501) in your browser.

Both containers are reachable only from this machine: Valkey publishes no port (the app
reaches it over the Docker network) and the app is published on `127.0.0.1` only. Neither
has authentication, so don't publish them on other interfaces.

If you're on a remote dev desktop, forward port 8501 to your local machine:
```bash
# SSH tunnel
ssh -L 8501:localhost:8501 user@your-dev-host
```

### 4. Sample data

Each web UI page creates its own index and catalog the first time you open it. The Cursors
page generates 100,000 products, and the semantic pages download the embedding model
(all-MiniLM-L6-v2) on first use, so open each page once before presenting.

### 5. Tear down

```bash
docker stop valkey-search-demo valkey-search-demo-app
docker rm valkey-search-demo valkey-search-demo-app
docker network rm valkey-demo-net
```

## Building libsearch.so

The valkey-search 1.3 module requires Valkey >= 9.1.0 (`valkey/valkey:unstable` Docker image) and must be built in a Linux environment compatible with the target container (Debian).

### Option A: Build using the valkey-search dev container (recommended)

If you have [valkey-search](https://github.com/valkey-io/valkey-search) checked out locally with the dev container image built:

```bash
cd /path/to/valkey-search
git checkout upstream/1.3

# Configure and build just the module inside the dev container
docker run --rm -v $(pwd):/workspace -w /workspace valkey-search-dev:latest \
  bash -c "./build.sh --debug --configure --no-build && cd .build-debug && ninja libsearch.so"

# Copy the built module
cp .build-debug/libsearch.so /path/to/valkey-search-demo/
```

### Option B: Build natively on a Debian/Ubuntu host

```bash
cd /path/to/valkey-search
git checkout upstream/1.3

# Install dependencies (see valkey-search README for full list)
sudo apt install -y build-essential g++-12 cmake ninja-build libssl-dev

./build.sh
cp .build-release/libsearch.so /path/to/valkey-search-demo/
```

## Running without Docker

If you prefer to run natively:

```bash
# 1. Start Valkey (>= 9.1.0) with the search module
valkey-server --loadmodule /path/to/libsearch.so --save "" --appendonly no

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Run the Streamlit web UI
streamlit run app.py

# 4. Or run the interactive CLI
python -m demo.cli
```

## Project Structure

```
valkey-search-demo/
├── app.py                    # Streamlit web UI
├── docker-compose.yml        # Docker orchestration
├── Dockerfile                # App container image
├── requirements.txt
├── libsearch.so              # valkey-search module (you build this)
├── data/                     # Generated at runtime by data loader
├── core/
│   ├── config.py             # Connection settings, index names
│   ├── client.py             # Valkey client wrapper
│   ├── data_loader.py        # Sample data generation + embedding
│   └── index_manager.py      # FT.CREATE / FT.DROPINDEX
├── demo_pages/               # Web UI pages, one per 1.3 feature
│   ├── common.py             # Shared storefront cards, banners, helpers
│   ├── catalog.py            # Product catalogs for every page
│   ├── multilang.py          # Localized storefront
│   ├── scoring.py            # BM25STD without vs with ranking
│   ├── cursors.py            # Load more + offset vs cursor timing
│   ├── hybrid.py             # Keyword vs semantic vs FT.HYBRID
│   └── vector_range.py       # KNN vs VECTOR_RANGE recommendations
├── features/                 # Older per-feature modules, used by the CLI
│   ├── base.py               # Abstract base class for demos
│   ├── multilang_fts.py      # Multi-language FTS (Snowball stemmers)
│   ├── bm25_scoring.py       # BM25STD scoring with WITHSCORES
│   ├── vector_search.py      # BFLOAT16 vectors + range queries
│   ├── hybrid_search.py      # FT.HYBRID with RRF/LINEAR fusion
│   └── cursor_paging.py      # WITHCURSOR pagination
├── demo/
│   └── cli.py                # Interactive CLI demo runner
└── tests/
    └── test_features.py
```

## License

Apache 2.0
