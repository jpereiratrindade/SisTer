const state = {
  currentUser: window.__sisterUser || null,
  surfaces: [],
  semanticParticipants: [],
  semanticSourceStatus: "not_loaded",
  semanticLoaded: false
};

const qs = (selector) => document.querySelector(selector);
const qsa = (selector) => [...document.querySelectorAll(selector)];

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = String(value ?? "");
  return element.innerHTML;
}

function initials(name) {
  return String(name || "ST")
    .split(/[\s_-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function showAuthenticatedIdentity(user) {
  state.currentUser = user;
  document.body.classList.remove("auth-pending", "public-mode");
  document.body.classList.add("authenticated-mode");
  qs("#public-home").hidden = true;
  qs("#authenticated-workspace").hidden = false;
  qs("#app-sidebar").hidden = false;
  qs("#auth-login").hidden = true;
  qs("#auth-identity").hidden = false;
  qs("#auth-avatar").hidden = false;
  qs("#auth-name").textContent = user.name;
  qs("#auth-avatar").textContent = initials(user.name);
  qsa("[data-admin-only]").forEach((item) => {
    item.hidden = user.role !== "admin";
  });
  renderHomeContext();
}

function availabilityLabel(value) {
  if (value === "available") return "Disponível";
  if (value === "unavailable") return "Temporariamente indisponível";
  return "Disponibilidade não observada";
}

function readableRole(value) {
  const role = String(value || "").trim();
  if (!role) return "Não declarado";
  return role.replace(/[_-]+/g, " ");
}

function renderHomeContext() {
  const user = state.currentUser;
  if (!user) return;
  const firstName = String(user.name || "").trim().split(/\s+/)[0] || "usuário";
  const greeting = qs("#home-greeting");
  const name = qs("#home-context-name");
  const role = qs("#home-context-role");
  if (greeting) greeting.textContent = `Olá, ${firstName}.`;
  if (name) name.textContent = user.name || "Não declarada";
  if (role) role.textContent = readableRole(user.role);
}

function renderWorkspace() {
  const container = qs("#workspace-resources");
  if (!container) return;

  const total = state.surfaces.length;
  const available = state.surfaces.filter((surface) => surface.availability === "available").length;
  const resourceSummary = qs("#home-context-resources");
  if (resourceSummary) {
    resourceSummary.textContent = total === 0
      ? "0"
      : `${available} disponíveis · ${total} visíveis`;
  }

  if (total === 0) {
    container.innerHTML = `
      <article class="workspace-empty experience-workspace-empty">
        <h4>Nenhum recurso disponível para este perfil</h4>
        <p>Recursos aparecem aqui somente quando possuem finalidade, endereço público e autorização declarados.</p>
      </article>`;
    return;
  }

  container.innerHTML = state.surfaces.map((surface) => {
    const label = surface.label || "Participante";
    const purpose = surface.purpose || "Capacidade declarada para este contexto.";
    return `
      <article class="workspace-resource-card experience-surface-card">
        <div class="experience-surface-provider">
          <span class="system-mark" aria-hidden="true">${escapeHtml(initials(label))}</span>
          <div><span>Fornecido por</span><strong>${escapeHtml(label)}</strong></div>
        </div>
        <div class="experience-surface-content">
          <h4>${escapeHtml(purpose)}</h4>
          <span class="workspace-availability" data-availability="${escapeHtml(surface.availability)}">
            ${escapeHtml(availabilityLabel(surface.availability))}
          </span>
        </div>
        <a class="primary-action" href="${escapeHtml(surface.public_url)}">Abrir</a>
      </article>`;
  }).join("");
}

function renderSemanticEcosystem() {
  const container = qs("#semantic-ecosystem");
  if (!container) return;
  if (state.semanticParticipants.length === 0) {
    const detail = state.semanticSourceStatus === "authoritative"
      ? "A fonte vigente não declarou participantes visíveis neste contexto."
      : "Nenhuma fonte semântica autoritativa está disponível para esta projeção.";
    container.innerHTML = `
      <article class="workspace-empty">
        <h4>Nenhum fato semântico disponível</h4>
        <p>${escapeHtml(detail)} Nenhuma relação foi inferida do deployment.</p>
      </article>`;
    return;
  }

  container.innerHTML = state.semanticParticipants.map((participant) => {
    const capabilities = Array.isArray(participant.capabilities) ? participant.capabilities : [];
    return `
      <article class="semantic-participant-card">
        <div class="semantic-participant-heading">
          <span class="system-mark" aria-hidden="true">${escapeHtml(initials(participant.label))}</span>
          <div><h4>${escapeHtml(participant.label)}</h4><p>${escapeHtml(participant.declared_state)}</p></div>
        </div>
        <dl>
          <div><dt>Autoridade</dt><dd>${escapeHtml(participant.authority_scope)}</dd></div>
          <div><dt>Proveniência</dt><dd>${escapeHtml(participant.provenance_ref)}</dd></div>
        </dl>
        <div class="semantic-capabilities">
          <strong>Capacidades declaradas</strong>
          ${capabilities.length > 0
            ? `<ul>${capabilities.map((capability) => `<li>${escapeHtml(capability.label)} <span>${escapeHtml(capability.authority_scope)}</span></li>`).join("")}</ul>`
            : "<p>Nenhuma capacidade declarada nesta projeção.</p>"}
        </div>
      </article>`;
  }).join("");
}

async function loadSemanticEcosystem() {
  if (state.semanticLoaded) return;
  state.semanticLoaded = true;
  try {
    const response = await fetch("/api/v1/ecosystem/semantic", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const view = await response.json();
    state.semanticParticipants = Array.isArray(view.participants) ? view.participants : [];
    state.semanticSourceStatus = view.source_status || "invalid";
  } catch {
    state.semanticParticipants = [];
    state.semanticSourceStatus = "unavailable";
  }
  renderSemanticEcosystem();
}

function openView(viewName) {
  qsa(".view").forEach((view) => view.classList.toggle("active", view.id === `view-${viewName}`));
  qsa("button.nav-link[data-view]").forEach((button) => {
    button.classList.toggle("selected", button.dataset.view === viewName);
  });
  if (viewName === "ecosystem") loadSemanticEcosystem();
}

async function loadWorkspace() {
  try {
    const response = await fetch("/api/v1/workspace", {cache: "no-store"});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const workspace = await response.json();
    state.surfaces = Array.isArray(workspace.surfaces) ? workspace.surfaces : [];
  } catch {
    state.surfaces = [];
  }
  renderWorkspace();
}

async function logout() {
  await fetch("/api/auth/logout", {method: "POST"}).catch(() => {});
  window.location.href = "/";
}

async function init() {
  if (!state.currentUser) {
    window.location.reload();
    return;
  }
  showAuthenticatedIdentity(state.currentUser);
  qs("#auth-logout")?.addEventListener("click", logout);
  qsa("button.nav-link[data-view]").forEach((button) => {
    button.addEventListener("click", () => openView(button.dataset.view));
  });
  qsa("[data-open-view]").forEach((button) => {
    button.addEventListener("click", () => openView(button.dataset.openView));
  });
  await loadWorkspace();
}

init();
