# TradingAgents Docker Image
# Multi-stage build for optimized image size with vnstock support

# ============================================================================
# Stage 1: Builder stage - install all dependencies
# ============================================================================
FROM python:3.10-slim-bookworm AS builder

# Install system dependencies required for:
# - Building Python packages with C extensions
# - vnstock library dependencies
# - Web scraping (beautifulsoup4, requests)
# - TA-Lib for technical analysis (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create virtual environment for clean dependency management
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip to latest version
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy dependency files first for better layer caching
COPY pyproject.toml requirements.txt ./

# Install Python dependencies from pyproject.toml
# Using pip install . after copying the full project would be ideal,
# but for caching we install from requirements first
RUN pip install --no-cache-dir -r requirements.txt

# Install vnstock library for Vietnamese stock market data
# vnstock3 is the latest version with improved API
RUN pip install --no-cache-dir vnstock3 || pip install --no-cache-dir vnstock

# Install additional dependencies for Vietnam market support
RUN pip install --no-cache-dir \
    beautifulsoup4>=4.12.0 \
    lxml>=5.0.0 \
    python-dotenv>=1.0.0

# ============================================================================
# Stage 2: Runtime stage - minimal image with only runtime dependencies
# ============================================================================
FROM python:3.10-slim-bookworm AS runtime

# Install only runtime dependencies
# - libxml2 and libxslt for lxml (web scraping)
# - ca-certificates for HTTPS requests
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash tradingagents \
    && mkdir -p /app /data /cache \
    && chown -R tradingagents:tradingagents /app /data /cache

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # TradingAgents configuration
    TRADINGAGENTS_RESULTS_DIR="/data/results" \
    TRADINGAGENTS_CACHE_DIR="/cache" \
    # Default market (can be overridden: "us" or "vn")
    TRADINGAGENTS_MARKET="vn"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=tradingagents:tradingagents . .

# Install the application package
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p /data/results /cache/data_cache \
    && chown -R tradingagents:tradingagents /data /cache

# Switch to non-root user
USER tradingagents

# Default port for CLI/API (if applicable)
EXPOSE 8000

# Health check - verify Python and key dependencies are working
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import tradingagents; print('healthy')" || exit 1

# Default command - run the CLI
# Override with docker run command for different entry points
CMD ["python", "main.py"]
