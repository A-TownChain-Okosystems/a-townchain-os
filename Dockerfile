FROM python:3.12-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ libssl-dev git
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
LABEL maintainer="ShivaCore <dev@atownchain.io>"
LABEL org.opencontainers.image.version="3.0.0"
RUN useradd -m -u 1000 atcnode
WORKDIR /app
COPY --from=builder /root/.local /home/atcnode/.local
COPY --chown=atcnode:atcnode . .
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3   CMD curl -f http://localhost:4000/health || exit 1
EXPOSE 3000 4000 4001 5005 8080 9090 9944
USER atcnode
ENV PATH="/home/atcnode/.local/bin:$PATH" ATC_CHAIN_ID=9000 ATC_ENV=production
ENTRYPOINT ["python","start.py"]
CMD ["--mode","fullnode","--chain-id","9000"]
