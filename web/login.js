const form = document.querySelector("#auth-form");
const error = document.querySelector("#auth-error");
let bootstrap = false;

async function initializeLogin() {
  try {
    const response = await fetch("/api/auth/bootstrap", {cache: "no-store"});
    if (!response.ok) throw new Error();
    bootstrap = (await response.json()).open;
    if (!bootstrap) return;

    document.querySelector("#form-title").textContent = "Crie a conta administradora";
    document.querySelector("#form-lead").textContent =
      "Este é o primeiro acesso. A conta criada administrará as visões internas do SisTer.";
    document.querySelector("#name-field").hidden = false;
    document.querySelector("[name=name]").required = true;
    document.querySelector("[name=password]").minLength = 12;
    document.querySelector("[name=password]").autocomplete = "new-password";
    document.querySelector("#submit-label").textContent = "Criar conta e entrar";
  } catch {
    error.textContent = "O serviço de identidade não está disponível.";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  error.textContent = "";
  const button = form.querySelector("button");
  button.disabled = true;
  const body = Object.fromEntries(new FormData(form));

  try {
    const response = await fetch(
      bootstrap ? "/api/auth/register" : "/api/auth/login",
      {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
      }
    );
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.detail || "Não foi possível entrar.");
    window.location.href = "/";
  } catch (reason) {
    error.textContent = reason.message;
  } finally {
    button.disabled = false;
  }
});

initializeLogin();
