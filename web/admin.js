const form = document.querySelector("#user-form");
const message = document.querySelector("#admin-message");
const tbody = document.querySelector("#users");

function escapeHtml(value) {
  const element = document.createElement("div");
  element.textContent = value;
  return element.innerHTML;
}

async function ensureAdmin() {
  const response = await fetch("/api/me", {cache: "no-store"});
  if (response.status === 401) {
    window.location.href = "/login";
    return false;
  }
  const user = await response.json();
  if (!response.ok || user.role !== "admin") {
    window.location.href = "/";
    return false;
  }
  return true;
}

async function loadUsers() {
  const response = await fetch("/api/admin/users", {cache: "no-store"});
  if (response.status === 401) {
    window.location.href = "/login";
    return;
  }
  if (response.status === 403) {
    window.location.href = "/";
    return;
  }
  const users = await response.json();
  tbody.innerHTML = users.map((user) => `
    <tr>
      <td><strong>${escapeHtml(user.name)}</strong></td>
      <td>${escapeHtml(user.email)}</td>
      <td><span class="role-pill role-pill--${user.role}">${user.role === "admin" ? "Administrador" : "Usuário"}</span></td>
    </tr>
  `).join("");
  document.querySelector("#user-count").textContent =
    `${users.length} ${users.length === 1 ? "pessoa" : "pessoas"}`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "";
  const button = form.querySelector("button");
  button.disabled = true;
  try {
    const response = await fetch("/api/admin/users", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(Object.fromEntries(new FormData(form)))
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || "Não foi possível criar o acesso.");
    form.reset();
    message.textContent = "Acesso criado com sucesso.";
    await loadUsers();
  } catch (reason) {
    message.textContent = reason.message;
  } finally {
    button.disabled = false;
  }
});

ensureAdmin().then((allowed) => {
  if (allowed) loadUsers();
});
