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

const WHATSAPP_NUMBER = "51902126765";

function buildLeadMessage(data) {
  return [
    "Hola, solicito un análisis exportador con CLI Market Export Intelligence.",
    "",
    `Nombre: ${data.nombre}`,
    `Empresa: ${data.empresa || "-"}`,
    `Correo: ${data.correo}`,
    `WhatsApp: ${data.whatsapp || "-"}`,
    `Producto: ${data.producto}`,
    `Mercado destino: ${data.mercado}`,
    `Etapa: ${data.etapa}`,
  ].join("\n");
}

const leadForm = document.getElementById("lead-form");
const leadStatus = document.getElementById("lead-status");
if (leadForm) {
  leadForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(leadForm).entries());
    const message = encodeURIComponent(buildLeadMessage(data));
    window.open(`https://wa.me/${WHATSAPP_NUMBER}?text=${message}`, "_blank", "noopener,noreferrer");
    if (leadStatus) {
      leadStatus.textContent = "Se abrió WhatsApp con tu solicitud prellenada. Solo envía el mensaje.";
      leadStatus.classList.remove("hidden");
    }
  });
}

const whatsappFloat = document.querySelector(".whatsapp-float");
if (whatsappFloat) {
  const intro = encodeURIComponent(
    "Hola, me interesa un análisis exportador con CLI Market Export Intelligence.",
  );
  whatsappFloat.href = `https://wa.me/${WHATSAPP_NUMBER}?text=${intro}`;
}

const revealTargets = document.querySelectorAll("main > section:not(.hero)");
if (revealTargets.length) {
  revealTargets.forEach((section) => section.classList.add("reveal"));
  const revealObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -80px 0px" },
  );
  revealTargets.forEach((section) => revealObserver.observe(section));
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
