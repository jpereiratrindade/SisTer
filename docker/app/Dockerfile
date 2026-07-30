FROM fedora:44 AS builder

RUN dnf install -y \
    cmake \
    ninja-build \
    gcc-c++ \
    openssl-devel \
    libpq-devel \
    && dnf clean all

WORKDIR /src
COPY . .

RUN cmake -S . -B build -G Ninja \
        -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build --target sisterd sisterctl \
    && ctest --test-dir build --output-on-failure

# ── Runtime image ──────────────────────────────────────────────────────────────
FROM fedora:44

RUN dnf install -y libpq && dnf clean all

WORKDIR /app

COPY --from=builder /src/build/apps/sisterd/sisterd   ./sisterd
COPY --from=builder /src/build/apps/sisterctl/sisterctl ./sisterctl
COPY web/ ./web/

ENV SISTER_BIND_HOST=0.0.0.0
ENV SISTER_PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
    CMD curl -sf http://localhost:8000/api/health || exit 1

ENTRYPOINT ["./sisterd"]
CMD ["8000", "web"]
