(() => {
  const root = document.documentElement;
  const nav = document.querySelector('[data-nav]');
  const navToggle = document.querySelector('[data-nav-toggle]');
  const themeToggle = document.querySelector('[data-theme-toggle]');
  const storedTheme = localStorage.getItem('sister-theme');

  if (storedTheme === 'dark' || storedTheme === 'light') {
    root.dataset.theme = storedTheme;
  }

  navToggle?.addEventListener('click', () => {
    const open = nav?.dataset.open !== 'true';
    if (nav) nav.dataset.open = String(open);
    navToggle.setAttribute('aria-expanded', String(open));
  });

  nav?.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      nav.dataset.open = 'false';
      navToggle?.setAttribute('aria-expanded', 'false');
    });
  });

  themeToggle?.addEventListener('click', () => {
    const current = root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const next = current === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    localStorage.setItem('sister-theme', next);
  });

  const links = [...document.querySelectorAll('.site-nav a[href^="#"]')];
  const sections = links.map((link) => document.querySelector(link.getAttribute('href'))).filter(Boolean);
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      links.forEach((link) => link.removeAttribute('aria-current'));
      const active = links.find((link) => link.getAttribute('href') === `#${entry.target.id}`);
      active?.setAttribute('aria-current', 'true');
    });
  }, { rootMargin: '-25% 0px -65% 0px' });
  sections.forEach((section) => observer.observe(section));
})();
