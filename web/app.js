const state = {
  systems: [
    {
      id: "morfocampo",
      name: "MorfoCampo",
      version: "0.2.1",
      type: "Sistema autonomo de campo",
      contract: "sister-contracts/0.1.0",
      domains: ["campo_nativo", "silvipastoril", "observacao_campo"],
      modes: ["offline", "local_network", "camponode"],
      exports: ["observations", "evidence", "audio", "photos", "field_notes", "spatial_context"],
      policy: ["proveniencia", "schema", "offline"]
    },
    {
      id: "droneops",
      name: "DroneOps",
      version: "0.1.0",
      type: "Sistema autonomo de missao",
      contract: "sister-contracts/0.1.0",
      domains: ["drone", "imageamento", "missao_campo", "evidencia_geoespacial"],
      modes: ["offline", "local_network", "pwa", "embedded_server"],
      exports: ["mission_plan", "flight_log", "images", "spatial_layers", "evidence_package"],
      policy: ["proveniencia", "schema", "operador", "referencia_espacial"]
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
    }
  ]
};

const qs = (selector, root = document) => root.querySelector(selector);
const qsa = (selector, root = document) => [...root.querySelectorAll(selector)];

function setCounts() {
  qs("#contract-count").textContent = state.contracts.length;
  qs("#system-count").textContent = state.systems.length;
  qs("#evidence-count").textContent = state.evidence.length;
}

function renderSystems(filter = "") {
  const normalized = filter.trim().toLowerCase();
  const systems = state.systems.filter((system) => {
    const haystack = [
      system.name,
      system.id,
      system.type,
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
      <h3>${system.name}</h3>
      <p class="system-meta">${system.type} · ${system.version} · ${system.contract}</p>
      <div class="tag-row" aria-label="Dominios">
        ${system.domains.map((item) => `<span class="tag">${item}</span>`).join("")}
      </div>
      <p class="system-meta">Modos: ${system.modes.join(", ")}</p>
      <p class="system-meta">Exports: ${system.exports.join(", ")}</p>
    </article>
  `).join("");
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
  ctx.fillStyle = "#dfe9e3";
  ctx.fillRect(0, 0, w, h);

  ctx.fillStyle = "#c7d9ce";
  ctx.beginPath();
  ctx.moveTo(80, 410);
  ctx.bezierCurveTo(180, 260, 320, 310, 410, 170);
  ctx.bezierCurveTo(560, -10, 760, 130, 820, 260);
  ctx.bezierCurveTo(760, 390, 610, 420, 460, 380);
  ctx.bezierCurveTo(300, 340, 210, 500, 80, 410);
  ctx.fill();

  ctx.strokeStyle = "#497aa6";
  ctx.lineWidth = 18;
  ctx.beginPath();
  ctx.moveTo(0, 120);
  ctx.bezierCurveTo(180, 150, 250, 90, 380, 126);
  ctx.bezierCurveTo(520, 170, 600, 280, 900, 245);
  ctx.stroke();

  const plots = [
    { x: 240, y: 265, w: 150, h: 84, color: "#8bb58f", label: "Campo nativo" },
    { x: 445, y: 180, w: 180, h: 100, color: "#c2ad7c", label: "Silvipastoril" },
    { x: 565, y: 315, w: 150, h: 76, color: "#89a9c6", label: "Voo DroneOps" }
  ];

  plots.forEach((plot) => {
    ctx.fillStyle = plot.color;
    ctx.strokeStyle = "#263d35";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.roundRect(plot.x, plot.y, plot.w, plot.h, 12);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#17211d";
    ctx.font = "700 18px sans-serif";
    ctx.fillText(plot.label, plot.x + 18, plot.y + 42);
  });

  const points = [
    { x: 290, y: 308, label: "M01", color: "#1d7662" },
    { x: 505, y: 225, label: "D01", color: "#a9443d" },
    { x: 654, y: 354, label: "L01", color: "#114c42" }
  ];

  points.forEach((point) => {
    ctx.fillStyle = point.color;
    ctx.beginPath();
    ctx.arc(point.x, point.y, 13, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#ffffff";
    ctx.font = "700 11px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(point.label, point.x, point.y);
  });

  ctx.textAlign = "start";
  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = "#31463d";
  ctx.font = "600 16px sans-serif";
  ctx.fillText("Camadas: observacoes, evidencias, contexto espacial", 28, 42);
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
    showToast("Amostra valida: sistemas possuem contrato, dominio e proveniencia declarada.");
  } else {
    showToast(`Amostra com pendencias: ${invalid.map((system) => system.name).join(", ")}`);
  }
}

function bindNavigation() {
  qsa(".nav-tab").forEach((button) => {
    button.addEventListener("click", () => {
      qsa(".nav-tab").forEach((item) => item.classList.remove("active"));
      qsa(".view").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      qs(`#view-${button.dataset.view}`).classList.add("active");
    });
  });
}

function init() {
  setCounts();
  renderSystems();
  renderContracts();
  renderEvidence();
  drawMap();
  bindNavigation();

  qs("#system-filter").addEventListener("input", (event) => renderSystems(event.target.value));
  qs("#validate-button").addEventListener("click", validateSample);
}

init();
