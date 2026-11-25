# syntax=docker/dockerfile:1.7
#
# Transport digital twin: HTTP API (port 9100) and MCP tools (port 8766).
#
#   docker build -t transport-twin .
#       with NS-3.45 and the Ceragon module built in (NS3_TWIN_MODE=local): pre-flight verdicts
#       come from real NS-3 runs. The first build compiles NS-3 (~10-20 min); later builds reuse it.
#
#   docker build --target replay -t transport-twin:replay .
#       without NS-3: answers from recorded runs (NS3_TWIN_RECORDINGS), which never decide a verdict

ARG PYTHON=3.12
ARG NS3_VERSION=ns-3.45

# ── NS-3.45 with the Ceragon module, only the modules it needs ───────────────────────────────
FROM python:${PYTHON}-slim AS ns3
ARG NS3_VERSION
RUN apt-get update \
 && apt-get install -y --no-install-recommends g++ cmake ninja-build git ca-certificates binutils \
 && rm -rf /var/lib/apt/lists/*
RUN git clone --depth 1 --branch "${NS3_VERSION}" https://github.com/nsnam/ns-3-dev-git /opt/ns3
WORKDIR /opt/ns3
COPY ns3_ceragon/contrib/ceragon/ contrib/ceragon/
RUN cp contrib/ceragon/examples/ceragon-twin-from-file.cc scratch/ceragon-twin.cc \
 && ./ns3 configure -d release -G Ninja --disable-examples --disable-tests --disable-python-bindings --enable-modules=ceragon \
 && cmake --build cmake-cache -j "$(nproc)" \
 && strip --strip-unneeded build/scratch/ns3.45-ceragon-twin build/lib/*.so \
 && build/scratch/ns3.45-ceragon-twin --PrintHelp > /dev/null

# ── the twin's API ────────────────────────────────────────────────────────────────────────────
FROM python:${PYTHON}-slim AS replay
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt "mcp>=1.2"

COPY src/ src/
COPY ns3_ceragon/ ns3_ceragon/
COPY data/ data/

RUN useradd --uid 10001 --create-home twin && chown -R twin /app
USER twin

ENV TWIN_PORT=9100 \
    TERAFLOW_URL=http://teraflowsdn-nbi:80 \
    TWIN_TOPOLOGY_SOURCE=rfc8345 \
    TWIN_DESCRIPTORS=/app/data/6g_transport_tfs_descriptors.json \
    NS3_TWIN_MODE=replay

LABEL org.opencontainers.image.title="Transport digital twin" \
      org.opencontainers.image.source="https://github.com/efidvir/tfs-ns3-digital-twin"

EXPOSE 9100 8766
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"TWIN_PORT\",\"9100\")}/healthz', timeout=4)"

# HTTP API by default; run the MCP tools with:
#   docker run ... python src/twin_mcp.py --transport streamable-http --host 0.0.0.0
CMD ["python", "src/tfs_digital_twin_api.py"]

# ── default: the API with NS-3 (the binary keeps its library path, /opt/ns3/build/lib) ─────────
FROM replay AS app
COPY --from=ns3 /opt/ns3/build/lib/ /opt/ns3/build/lib/
COPY --from=ns3 /opt/ns3/build/scratch/ns3.45-ceragon-twin /opt/ns3/build/scratch/ns3.45-ceragon-twin
ENV NS3_DIR=/opt/ns3 \
    NS3_TWIN_MODE=local \
    CERAGON_TWIN_BINARY=/opt/ns3/build/scratch/ns3.45-ceragon-twin
