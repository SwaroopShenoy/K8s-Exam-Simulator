FROM python:3.11-slim

# Install kubectl
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    curl -fsSL "https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
         -o /usr/local/bin/kubectl && \
    chmod +x /usr/local/bin/kubectl && \
    apt-get purge -y curl && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pyyaml

WORKDIR /app

COPY simulator.py .
COPY questions/ questions/

RUN mkdir -p workspace

ENTRYPOINT ["python3", "simulator.py"]
CMD ["--help"]
