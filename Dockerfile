FROM python:3.12-slim

WORKDIR /app

# Install deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary=:all: \
        scipy scikit-learn && \
    pip install --no-cache-dir -r requirements.txt

# Bake the embedding model into the image so runtime never hits HF Hub
# (unauthenticated HF requests are rate-limited and can fail, wedging the demo).
ENV HF_HOME=/opt/hf-cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Use only the baked cache at runtime: fail fast and loud if a model is missing,
# instead of stalling on a throttled download.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

# Copy application code
COPY core/ core/
COPY demo/ demo/
COPY demo_pages/ demo_pages/
COPY features/ features/
COPY tests/ tests/
COPY app.py .

# Create empty data dir (generated at runtime)
RUN mkdir -p data

ENV VALKEY_HOST=valkey
ENV VALKEY_PORT=6379

EXPOSE 8501

CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true"]
