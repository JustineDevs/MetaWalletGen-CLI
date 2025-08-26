# MetaWalletGen CLI Docker Image
# Version: 2.0.0

FROM python:3.11-slim

LABEL maintainer="MetaWalletGen Team <maintainers@metawalletgen.com>"
LABEL version="2.0.0"
LABEL description="Professional Ethereum Wallet Generator with Advanced Security Features"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package files
COPY . .

# Install the package
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd --create-home --shell /bin/bash metawalletgen
USER metawalletgen

# Set entry point
ENTRYPOINT ["metawalletgen"]

# Default command
CMD ["--help"]
