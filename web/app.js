const state = {
  systems: [
    {
      id: "morfocampo",
      name: "MorfoCampo",
      version: "0.2.1",
      owner: "Equipe Campo",
      type: "Campo",
      status: "Operacional",
      contract: "sister-contracts/0.1.0",
      accessUrl: "https://morfocampo.local",
      accessMode: "Restrito",
      publicScope: "Indicadores agregados",
      restrictedScope: "Observacoes e metadados",
      privateScope: "Midia bruta e notas",
      domains: ["campo_nativo", "silvipastoril", "observacao_campo"],
      modes: ["offline", "local_network", "camponode"],
      exports: ["observations", "evidence", "photos", "field_notes", "spatial_context"],
      policy: ["proveniencia", "schema", "offline"],
      infra: {
        availability: "98%",
        response: "sync 12 min",
        storage: "41%",
        lastCheck: "09:20",
        signal: "ok"
      }
    },
    {
      id: "droneops",
      name: "DroneOps",
      version: "0.1.0",
      owner: "Equipe Geoespacial",
      type: "Missao",
      status: "Em validacao",
      contract: "sister-contracts/0.1.0",
      accessUrl: "https://droneops.local",
      accessMode: "Restrito",
      publicScope: "Cobertura generalizada",
      restrictedScope: "Camadas e logs resumidos",
      privateScope: "Imagens brutas e operador",
      domains: ["drone", "imageamento", "missao_campo", "evidencia_geoespacial"],
      modes: ["offline", "local_network", "pwa"],
      exports: ["mission_plan", "flight_log", "images", "spatial_layers", "evidence_package"],
      policy: ["proveniencia", "schema", "operador", "referencia_espacial"],
      infra: {
        availability: "91%",
        response: "sync 28 min",
        storage: "63%",
        lastCheck: "09:12",
        signal: "warn"
      }
    },
    {
      id: "camponode",
      name: "CampoNode",
      version: "0.1.0",
      owner: "Infraestrutura",
      type: "Infraestrutura",
      status: "Planejado",
      contract: "sister-contracts/0.1.0",
      accessUrl: "https://camponode.local",
      accessMode: "Rede local",
      publicScope: "Status agregado",
      restrictedScope: "Saude do no e cache",
      privateScope: "Logs operacionais",
      domains: ["rede_local", "armazenamento", "sincronizacao"],
      modes: ["offline", "local_network", "edge"],
      exports: ["sync_log", "node_health", "package_cache"],
      policy: ["proveniencia", "schema", "auditoria"],
      infra: {
        availability: "N/D",
        response: "planejado",
        storage: "N/D",
        lastCheck: "sem coleta",
        signal: "planned"
      }
    },
    {
      id: "radar_sister_resiliencia",
      name: "Radar-Sister Resiliencia",
      version: "0.1.0",
      owner: "Equipe Resiliencia",
      type: "Analitico",
      status: "Operacional",
      contract: "sister-contracts/0.1.0",
      accessUrl: "http://127.0.0.1:8765",
      accessMode: "Local",
      publicScope: "Links publicos e scores agregados",
      restrictedScope: "Shortlists, scores e trilhas",
      privateScope: "Sessoes, chaves e revisoes brutas",
      domains: ["resiliencia", "inteligencia_territorial", "adaptacao_climatica"],
      modes: ["local_gui", "local_cli", "postgresql_pgvector"],
      exports: ["normalized_metadata", "scores_jsonl", "shortlist_markdown", "audit_log", "vector_chunks"],
      policy: ["proveniencia", "schema", "operador", "vetorial"],
      infra: {
        availability: "96%",
        response: "127 ms",
        storage: "52%",
        lastCheck: "09:15",
        signal: "ok"
      }
    }
  ],
  contracts: [
    {
      name: "System Manifest",
      version: "0.1.0",
      required: "Sim",
      rule: "Todo sistema federado declara identidade, dominio, modos operacionais, exports e politica de dados."
    },
    {
      name: "CampoSync Package",
      version: "0.1.0",
      required: "Para ingestao offline",
      rule: "Pacote precisa conter origem, contrato, conteudo declarado, data de criacao e checksum."
    },
    {
      name: "Evidence",
      version: "0.1.0",
      required: "Para dado promovido",
      rule: "Evidencia vincula sistema produtor, objeto, tipo, URI, momento de captura e checksum quando aplicavel."
    }
  ],
  evidence: [
    {
      time: "2026-07-09 21:30",
      source: "MorfoCampo",
      object: "obs-001",
      kind: "photo",
      ref: "evidence/photos/obs-001.jpg",
      status: "proveniencia minima"
    },
    {
      time: "2026-07-09 21:42",
      source: "DroneOps",
      object: "mission-terrace-01",
      kind: "spatial_layer",
      ref: "evidence/layers/orthomosaic.geojson",
      status: "referencia espacial"
    },
    {
      time: "2026-07-09 22:05",
      source: "SisTer Core",
      object: "pkg-camposync-001",
      kind: "log",
      ref: "audit/validation_report.json",
      status: "schema validado"
    },
    {
      time: "2026-07-10 09:15",
      source: "Radar-Sister Resiliencia",
      object: "shortlist-resiliencia-001",
      kind: "document",
      ref: "data/exports/*_shortlist.md",
      status: "triagem auditavel"
    }
  ],
  integrationResults: [
    { label: "Manifestos reconhecidos", value: 100 },
    { label: "Proveniencia minima", value: 96 },
    { label: "Cobertura CampoSync", value: 82 },
    { label: "Prontidao para catalogo", value: 74 }
  ],
  services: [
    {
      name: "Contract Registry",
      summary: "Schemas, versoes e compatibilidade de contratos.",
      status: "operacional",
      score: 100
    },
    {
      name: "Package Ingest",
      summary: "Entrada de pacotes CampoSync e validacao de manifesto.",
      status: "em validacao",
      score: 78
    },
    {
      name: "Evidence Store",
      summary: "Rastreio de evidencias, checksums e referencias externas.",
      status: "operacional",
      score: 92
    },
    {
      name: "Territorial Catalog",
      summary: "Promocao de objetos territoriais confiaveis.",
      status: "planejado",
      score: 45
    },
    {
      name: "API Server",
      summary: "Exposicao REST para UI, integracoes locais e auditoria.",
      status: "planejado",
      score: 32
    },
    {
      name: "Governance Monitor",
      summary: "Sinais de ADR, DDD, DAI, politicas, LGPD e seguranca.",
      status: "operacional",
      score: 88
    }
  ]
};

const qs = (selector, root = document) => root.querySelector(selector);
const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];

function setCounts() {
  qs("#signed-contract-count").textContent = state.systems.length;
  qs("#system-count").textContent = state.systems.length;
  qs("#evidence-count").textContent = state.evidence.length;
  qs("#integration-compliance").textContent = "N/D";
}

function renderSystems(filter = "") {
  const normalized = filter.trim().toLowerCase();
  const systems = state.systems.filter((system) => {
    const haystack = [
      system.name,
      system.id,
      system.type,
      system.status,
      system.contract,
      ...system.domains,
      ...system.modes,
      ...system.exports,
      ...system.policy
    ].join(" ").toLowerCase();
    return haystack.includes(normalized);
  });

  qs("#systems-grid").innerHTML = systems.map((system) => `
    <article class="system-card">
      <h4>${system.name}</h4>
      <p class="system-meta">${system.type} · ${system.version} · ${system.status}</p>
      <div class="tag-row">
        ${system.domains.slice(0, 3).map((item) => `<span class="tag">${item}</span>`).join("")}
      </div>
      <div class="mini-table">
        <div><span>Owner</span><strong>${system.owner}</strong></div>
        <div><span>Contrato</span><strong>${system.contract}</strong></div>
        <div><span>Modo</span><strong>${system.modes.slice(0, 2).join(", ")}</strong></div>
        <div><span>Acesso</span><strong>${system.accessMode}</strong></div>
      </div>
      <div class="scope-list">
        <span><strong>Publico:</strong> ${system.publicScope}</span>
        <span><strong>Restrito:</strong> ${system.restrictedScope}</span>
        <span><strong>Privado:</strong> ${system.privateScope}</span>
      </div>
      <div class="infra-monitor">
        <div class="infra-title">
          <strong>Monitoramento</strong>
          <span class="status-dot ${system.infra.signal}">${system.infra.lastCheck}</span>
        </div>
        <div class="infra-grid">
          <span><strong>${system.infra.availability}</strong> disponibilidade</span>
          <span><strong>${system.infra.response}</strong> resposta/sync</span>
          <span><strong>${system.infra.storage}</strong> armazenamento</span>
        </div>
      </div>
      <a class="system-link" href="${system.accessUrl}" target="_blank" rel="noreferrer">Acessar plataforma</a>
    </article>
  `).join("");
}

function renderIntegrationBars() {
  qs("#integration-bars").innerHTML = state.integrationResults.map((item) => `
    <article class="result-item">
      <div class="result-row"><span>${item.label}</span><strong>${item.value}%</strong></div>
      <div class="bar-track"><div class="bar-fill" style="width: ${item.value}%"></div></div>
    </article>
  `).join("") + `
    <p class="panel-note">Valores demonstrativos. A avaliacao automatizada deve vir do validador de manifestos, ingestao CampoSync, proveniencia, schema, LGPD e diagnostico de servicos.</p>
  `;
}

function renderDiagnostics() {
  qs("#diagnostic-grid").innerHTML = state.services.map((service) => {
    const warn = service.score < 80 ? " warn" : "";
    return `
      <article class="diagnostic-card">
        <h3>${service.name}</h3>
        <p>${service.summary}</p>
        <div class="service-status">
          <span class="status-dot${warn}">${service.status}</span>
          <strong>${service.score}%</strong>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width: ${service.score}%"></div></div>
      </article>
    `;
  }).join("");
}

function renderContracts() {
  qs("#contracts-table").innerHTML = state.contracts.map((contract) => `
    <tr>
      <td>${contract.name}</td>
      <td>${contract.version}</td>
      <td>${contract.required}</td>
      <td>${contract.rule}</td>
    </tr>
  `).join("");
}

function renderEvidence() {
  qs("#evidence-list").innerHTML = state.evidence.map((item) => `
    <article class="timeline-item">
      <time>${item.time}</time>
      <div>
        <strong>${item.source} · ${item.object}</strong>
        <span>${item.kind} · ${item.ref}</span>
      </div>
      <span class="status-pill">${item.status}</span>
    </article>
  `).join("");
}

function drawMap() {
  const canvas = qs("#territory-map");
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#f8fbfd";
  ctx.fillRect(0, 0, w, h);

  ctx.fillStyle = "#e1edf2";
  ctx.beginPath();
  ctx.moveTo(60, 275);
  ctx.bezierCurveTo(190, 120, 370, 250, 510, 105);
  ctx.bezierCurveTo(690, -10, 870, 90, 1010, 210);
  ctx.bezierCurveTo(910, 345, 690, 305, 530, 275);
  ctx.bezierCurveTo(335, 238, 210, 360, 60, 275);
  ctx.fill();

  ctx.strokeStyle = "#1a7dc4";
  ctx.lineWidth = 14;
  ctx.beginPath();
  ctx.moveTo(0, 92);
  ctx.bezierCurveTo(170, 135, 260, 65, 420, 105);
  ctx.bezierCurveTo(600, 150, 730, 245, 1100, 206);
  ctx.stroke();

  const plots = [
    { x: 230, y: 168, w: 155, h: 82, color: "#b9dfd8", label: "MorfoCampo" },
    { x: 480, y: 120, w: 180, h: 86, color: "#d5e8f4", label: "DroneOps" },
    { x: 705, y: 220, w: 170, h: 74, color: "#e9d199", label: "CampoNode" }
  ];

  plots.forEach((plot) => {
    ctx.fillStyle = plot.color;
    ctx.strokeStyle = "#062d55";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(plot.x, plot.y, plot.w, plot.h, 10);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#09254b";
    ctx.font = "900 17px Avenir, sans-serif";
    ctx.fillText(plot.label, plot.x + 18, plot.y + 44);
  });

  const points = [
    { x: 292, y: 210, label: "M01", color: "#1c9b98" },
    { x: 560, y: 164, label: "D01", color: "#1a7dc4" },
    { x: 786, y: 258, label: "N01", color: "#e8a733" }
  ];

  points.forEach((point) => {
    ctx.fillStyle = point.color;
    ctx.beginPath();
    ctx.arc(point.x, point.y, 13, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.font = "900 11px Avenir, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(point.label, point.x, point.y);
  });

  ctx.textAlign = "start";
  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = "#536a80";
  ctx.font = "900 13px Avenir, sans-serif";
  ctx.fillText("Camadas: observacoes, evidencias, infraestrutura e contexto espacial", 24, 34);
}

function showToast(message) {
  const toast = qs("#toast");
  toast.textContent = message;
  toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("visible"), 3200);
}

function validateSample() {
  const invalid = state.systems.filter((system) => {
    return !system.id || !system.name || !system.contract || system.domains.length === 0 || !system.policy.includes("proveniencia");
  });

  if (invalid.length === 0) {
    showToast("Amostra valida: contrato, dominio, proveniencia e politica declarados.");
  } else {
    showToast(`Amostra com pendencias: ${invalid.map((system) => system.name).join(", ")}`);
  }
}

function bindNavigation() {
  qsa(".nav-link").forEach((button) => {
    button.addEventListener("click", () => {
      qsa(".nav-link").forEach((item) => item.classList.remove("selected"));
      qsa(".view").forEach((item) => item.classList.remove("active"));
      button.classList.add("selected");
      qs(`#view-${button.dataset.view}`).classList.add("active");
    });
  });
}

function init() {
  setCounts();
  renderSystems();
  renderIntegrationBars();
  renderDiagnostics();
  renderContracts();
  renderEvidence();
  drawMap();
  bindNavigation();

  qs("#system-filter").addEventListener("input", (event) => renderSystems(event.target.value));
  qs("#validate-button").addEventListener("click", validateSample);
}

init();
