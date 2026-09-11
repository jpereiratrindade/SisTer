const publicQs = (selector) => document.querySelector(selector);

const ecosystemSystems = {
  urt: {
    name: "URT",
    verb: "Observa",
    mark: "UR",
    summary: "Monitora territórios, fontes e eventos para transformar sinais do mundo real em dados confiáveis e rastreáveis.",
    flow: "Dados do mundo real",
    capabilities: ["Dados em tempo real", "Múltiplas fontes", "Rastreabilidade", "Territórios vivos"]
  },
  atmos: {
    name: "Atmos",
    verb: "Interpreta",
    mark: "AT",
    summary: "Analisa dados, extrai significado e identifica padrões relevantes no contexto territorial.",
    flow: "Significado",
    capabilities: ["Inteligência artificial", "Análise semântica", "Padrões e tendências", "Conhecimento acionável"]
  },
  nexo: {
    name: "Nexo",
    verb: "Apoia decisão",
    mark: "NX",
    summary: "Conecta evidências, cenários e alternativas para oferecer suporte qualificado e responsável à decisão.",
    flow: "Decisões com contexto",
    capabilities: ["Cenários e simulações", "Análise multicritério", "Recomendações contextuais", "Do dado à decisão"]
  },
  praxis: {
    name: "Praxis",
    verb: "Avalia",
    mark: "PX",
    summary: "Avalia resultados, monitora impactos e retroalimenta continuamente o ecossistema e as políticas.",
    flow: "Aprendizado e impacto",
    capabilities: ["Indicadores e métricas", "Avaliação de impactos", "Aprendizado contínuo", "Evolução de políticas"]
  }
};

const ecosystemContexts = {
  person: ["Pessoa", "Quem é, o que pesquisa e com quem colabora."],
  role: ["Papel", "Qual é sua função e sua autoridade no ecossistema."],
  project: ["Projeto", "O que busca realizar e quais resultados precisa produzir."],
  activity: ["Atividade", "Em que está trabalhando agora e quais capacidades são aplicáveis."],
  territory: ["Território", "Onde atua e em que contexto socioambiental."],
  period: ["Período", "Quando acontece e qual é o horizonte relevante."]
};

function openEcosystemSystem(systemKey) {
  const system = ecosystemSystems[systemKey];
  const dialog = publicQs("#system-dialog");
  if (!system || !dialog) return;

  publicQs("#system-dialog-mark").textContent = system.mark;
  publicQs("#system-dialog-type").textContent = system.verb;
  publicQs("#system-dialog-title").textContent = system.name;
  publicQs("#system-dialog-content").innerHTML = `
    <p class="dialog-summary">${system.summary}</p>
    <div class="detail-grid">
      <div><span>Fluxo no ecossistema</span><strong>${system.flow}</strong></div>
      <div><span>Relação com o SisTer</span><strong>Participante federado</strong></div>
    </div>
    <div class="detail-section">
      <span>Capacidades</span>
      <ul>${system.capabilities.map((capability) => `<li>${capability}</li>`).join("")}</ul>
    </div>
    <a class="dialog-action" href="/login">Entrar para acessar ${system.name}</a>`;

  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
}

function selectEcosystemContext(contextKey) {
  const context = ecosystemContexts[contextKey];
  if (!context) return;

  document.querySelectorAll("[data-context]").forEach((node) => {
    const selected = node.dataset.context === contextKey;
    node.classList.toggle("active", selected);
    node.setAttribute("aria-pressed", String(selected));
  });
  publicQs("#context-status-title").textContent = context[0];
  publicQs("#context-status-copy").textContent = context[1];
}

function initializeEcosystemExperience() {
  document.querySelectorAll("[data-system]").forEach((card) => {
    card.addEventListener("click", () => openEcosystemSystem(card.dataset.system));
  });
  document.querySelectorAll("[data-context]").forEach((node) => {
    node.addEventListener("click", () => selectEcosystemContext(node.dataset.context));
  });

  const dialog = publicQs("#system-dialog");
  publicQs("#system-dialog-close")?.addEventListener("click", () => dialog?.close());
  dialog?.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
  selectEcosystemContext("person");
}

function showPublicHome() {
  document.body.classList.remove("auth-pending", "authenticated-mode");
  document.body.classList.add("public-mode");
  publicQs("#public-home").hidden = false;
  publicQs("#authenticated-workspace").hidden = true;
  publicQs("#app-sidebar").hidden = true;
  publicQs("#auth-login").hidden = false;
  publicQs("#auth-identity").hidden = true;
  publicQs("#auth-avatar").hidden = true;
}

function loadAuthenticatedApplication() {
  const script = document.createElement("script");
  script.src = "/app.js";
  script.async = true;
  script.addEventListener("error", showPublicHome);
  document.body.append(script);
}

async function initializePublicBoundary() {
  try {
    const response = await fetch("/api/me", {cache: "no-store"});
    if (response.status === 401) {
      showPublicHome();
      return;
    }
    if (!response.ok) throw new Error();
    window.__sisterUser = await response.json();
    loadAuthenticatedApplication();
  } catch {
    showPublicHome();
  }
}

initializeEcosystemExperience();
initializePublicBoundary();
