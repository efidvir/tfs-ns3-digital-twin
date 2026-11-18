# Transport digital twin: HTTP API (port 9100) and MCP tools (port 8766)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt "mcp>=1.2"

COPY src/ src/
COPY ns3_ceragon/ ns3_ceragon/
COPY data/ data/

RUN useradd --uid 10001 --create-home twin && chown -R twin /app
USER twin

ENV TWIN_PORT=9100 \
    TERAFLOW_URL=http://teraflowsdn-nbi:80 \
    TWIN_TOPOLOGY_SOURCE=rfc8345 \
    TWIN_DESCRIPTORS=/app/data/6g_transport_tfs_descriptors.json

EXPOSE 9100 8766
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"TWIN_PORT\",\"9100\")}/healthz', timeout=4)"

# HTTP API by default; run the MCP tools with:
#   docker run ... python src/twin_mcp.py --transport streamable-http --host 0.0.0.0
CMD ["python", "src/tfs_digital_twin_api.py"]
