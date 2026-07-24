const publicQs = (selector) => document.querySelector(selector);

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
    loadAuthenticatedApplication();
  } catch {
    showPublicHome();
  }
}

initializePublicBoundary();
