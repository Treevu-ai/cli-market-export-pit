const nav = document.getElementById("nav");
const navToggle = document.getElementById("nav-toggle");
const mobileMenu = document.getElementById("mobile-menu");

if (navToggle && mobileMenu) {
  navToggle.addEventListener("click", () => {
    mobileMenu.classList.toggle("open");
  });
}

window.addEventListener("scroll", () => {
  if (!nav) return;
  nav.classList.toggle("scrolled", window.scrollY > 40);
});

document.querySelectorAll(".process-step").forEach((step) => {
  step.addEventListener("click", () => {
    document.querySelectorAll(".process-step").forEach((el) => el.classList.remove("active"));
    step.classList.add("active");
  });
});

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.tab;
    document.querySelectorAll(".tab").forEach((el) => el.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((el) => el.classList.remove("active"));
    tab.classList.add("active");
    const panel = document.getElementById(`tab-${target}`);
    if (panel) panel.classList.add("active");
  });
});

const leadForm = document.getElementById("lead-form");
const leadStatus = document.getElementById("lead-status");
if (leadForm) {
  leadForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(leadForm).entries());
    const subject = encodeURIComponent(`Solicitud análisis: ${data.producto || "producto"}`);
    const body = encodeURIComponent(
      `Nombre: ${data.nombre}\nEmpresa: ${data.empresa || "-"}\nCorreo: ${data.correo}\nWhatsApp: ${data.whatsapp || "-"}\nProducto: ${data.producto}\nMercado: ${data.mercado}\nEtapa: ${data.etapa}`,
    );
    window.location.href = `mailto:acuba0103@gmail.com?subject=${subject}&body=${body}`;
    if (leadStatus) {
      leadStatus.textContent = "Se abrió tu cliente de correo con el resumen del pedido.";
      leadStatus.classList.remove("hidden");
    }
  });
}

const sectionLinks = document.querySelectorAll('.nav-links a[href^="#"]');
const sections = [...sectionLinks].map((link) => document.querySelector(link.getAttribute("href"))).filter(Boolean);

if (sections.length) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const id = `#${entry.target.id}`;
        sectionLinks.forEach((link) => {
          link.classList.toggle("active", link.getAttribute("href") === id);
        });
      });
    },
    { rootMargin: "-40% 0px -50% 0px" },
  );
  sections.forEach((section) => observer.observe(section));
}
