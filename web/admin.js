const form = document.querySelector("#user-form");
const message = document.querySelector("#admin-message");
const tbody = document.querySelector("#users");

const editDialog = document.querySelector("#edit-dialog");
const editForm = document.querySelector("#edit-user-form");
const editMessage = document.querySelector("#edit-message");

const deleteDialog = document.querySelector("#delete-dialog");
const deleteConfirmBtn = document.querySelector("#delete-confirm-btn");
const deleteMessage = document.querySelector("#delete-message");

let currentUser = null;
let deletingUserId = null;

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
  currentUser = user;
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
  const roleLabels = {
    admin: "Administrador",
    project_lead: "Coordenador de Pesquisa",
    researcher: "Pesquisador",
    registered_user: "Usuário Registrado",
    user: "Usuário Registrado",
    guest: "Visitante"
  };
  tbody.innerHTML = users.map((user) => {
    const isSelf = currentUser && currentUser.id === user.id;
    return `
    <tr data-id="${user.id}">
      <td><strong>${escapeHtml(user.name)}</strong></td>
      <td>${escapeHtml(user.email)}</td>
      <td><span class="role-pill role-pill--${user.role}">${roleLabels[user.role] || escapeHtml(user.role)}</span></td>
      <td class="td-actions">
        <button type="button" class="btn-icon btn-edit" data-user='${escapeHtml(JSON.stringify(user))}' title="Editar usuário">
          ✏️ Editar
        </button>
        ${isSelf ? `
          <span class="badge-self" title="Sua conta logada">Você</span>
        ` : `
          <button type="button" class="btn-icon btn-delete" data-id="${user.id}" data-name="${escapeHtml(user.name)}" data-email="${escapeHtml(user.email)}" title="Excluir usuário">
            🗑️ Excluir
          </button>
        `}
      </td>
    </tr>
  `;
  }).join("");
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

// Manipuladores de Eventos da Tabela (Editar e Excluir)
tbody.addEventListener("click", (event) => {
  const editBtn = event.target.closest(".btn-edit");
  if (editBtn) {
    const user = JSON.parse(editBtn.dataset.user);
    openEditModal(user);
    return;
  }
  const deleteBtn = event.target.closest(".btn-delete");
  if (deleteBtn) {
    const { id, name, email } = deleteBtn.dataset;
    openDeleteModal(id, name, email);
    return;
  }
});

function openEditModal(user) {
  editMessage.textContent = "";
  document.querySelector("#edit-user-id").value = user.id;
  document.querySelector("#edit-name").value = user.name;
  document.querySelector("#edit-email").value = user.email;
  document.querySelector("#edit-role").value = user.role;
  document.querySelector("#edit-password").value = "";
  if (editDialog.showModal) editDialog.showModal();
  else editDialog.setAttribute("open", "true");
}

function closeEditModal() {
  if (editDialog.close) editDialog.close();
  else editDialog.removeAttribute("open");
}

document.querySelector("#edit-close-btn").addEventListener("click", closeEditModal);
document.querySelector("#edit-cancel-btn").addEventListener("click", closeEditModal);

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  editMessage.textContent = "";
  const id = document.querySelector("#edit-user-id").value;
  const payload = Object.fromEntries(new FormData(editForm));
  const saveBtn = editForm.querySelector("button[type='submit']");
  saveBtn.disabled = true;
  try {
    const response = await fetch(`/api/admin/users/${id}`, {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || "Não foi possível atualizar a pessoa.");
    closeEditModal();
    message.textContent = "Acesso atualizado com sucesso.";
    await loadUsers();
  } catch (reason) {
    editMessage.textContent = reason.message;
  } finally {
    saveBtn.disabled = false;
  }
});

function openDeleteModal(id, name, email) {
  deletingUserId = id;
  deleteMessage.textContent = "";
  document.querySelector("#delete-user-name").textContent = name;
  document.querySelector("#delete-user-email").textContent = email;
  if (deleteDialog.showModal) deleteDialog.showModal();
  else deleteDialog.setAttribute("open", "true");
}

function closeDeleteModal() {
  deletingUserId = null;
  if (deleteDialog.close) deleteDialog.close();
  else deleteDialog.removeAttribute("open");
}

document.querySelector("#delete-close-btn").addEventListener("click", closeDeleteModal);
document.querySelector("#delete-cancel-btn").addEventListener("click", closeDeleteModal);

deleteConfirmBtn.addEventListener("click", async () => {
  if (!deletingUserId) return;
  deleteMessage.textContent = "";
  deleteConfirmBtn.disabled = true;
  try {
    const response = await fetch(`/api/admin/users/${deletingUserId}`, {
      method: "DELETE"
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || "Não foi possível excluir o usuário.");
    closeDeleteModal();
    message.textContent = "Acesso removido com sucesso.";
    await loadUsers();
  } catch (reason) {
    deleteMessage.textContent = reason.message;
  } finally {
    deleteConfirmBtn.disabled = false;
  }
});

ensureAdmin().then((allowed) => {
  if (allowed) loadUsers();
});
