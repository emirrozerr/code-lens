FROM python:3.11-slim

# Install system dependencies
# Git is needed for GitPython (used in domain clustering later)
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY pyproject.toml .

# Copy the rest of the source code
COPY . .

# Install the application
RUN pip install -e .

# Expose the SSE port
EXPOSE 8000

# Run the MCP server over SSE, bound to all interfaces
CMD ["codelens", "mcp", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
