const state = {
  currentUser: window.__sisterUser || null,
  surfaces: []
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
}

function availabilityLabel(value) {
  if (value === "available") return "Disponível";
  if (value === "unavailable") return "Temporariamente indisponível";
  return "Disponibilidade não observada";
}

function renderWorkspace() {
  const container = qs("#workspace-resources");
  if (!container) return;

  if (state.surfaces.length === 0) {
    container.innerHTML = `
      <article class="workspace-empty">
        <h4>Nenhum recurso disponível para este perfil</h4>
        <p>Recursos aparecem aqui somente quando possuem finalidade, endereço público e autorização declarados.</p>
      </article>`;
    return;
  }

  container.innerHTML = state.surfaces.map((surface) => `
    <article class="workspace-resource-card">
      <span class="system-mark" aria-hidden="true">${escapeHtml(initials(surface.label))}</span>
      <div>
        <h4>${escapeHtml(surface.label)}</h4>
        <p>${escapeHtml(surface.purpose)}</p>
        <span class="workspace-availability" data-availability="${escapeHtml(surface.availability)}">
          ${escapeHtml(availabilityLabel(surface.availability))}
        </span>
      </div>
      <a class="primary-action" href="${escapeHtml(surface.public_url)}">Abrir</a>
    </article>`).join("");
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
  await loadWorkspace();
}

init();
