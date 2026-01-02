# LoanGuard Interest Validator - Docker Configuration
# Multi-stage build for production deployment

# Build stage
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r loanguard && useradd -r -g loanguard loanguard

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/loanguard/.local

# Copy application code
COPY --chown=loanguard:loanguard . .

# Create logs directory with proper permissions
RUN mkdir -p logs && chown -R loanguard:loanguard logs

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Switch to non-root user
USER loanguard

# Add local Python packages to PATH
ENV PATH=/home/loanguard/.local/bin:$PATH

# Set environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Labels for metadata
LABEL maintainer="LoanGuard Development Team"
LABEL version="1.0"
LABEL description="LoanGuard Interest Validator - Banking Tool for Interest Calculation Validation"

# Run the application
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=true"]