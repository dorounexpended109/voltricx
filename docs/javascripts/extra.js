/* ═══════════════════════════════════════════════════════════════════
   VOLTRICX — Production Interactions
   Particles · Scroll reveal · Orb parallax · Theme switcher · Counters
   ═══════════════════════════════════════════════════════════════════ */

/* ══════════════════════════════════════════════════════════════════
   THEME SWITCHER
   ══════════════════════════════════════════════════════════════════ */
const VTX_THEMES = [
  { name: "Violet", code: "violet", accent: "#7c3aed", a2: "#9d6eff", a3: "#c4b5fd", glow: "rgba(124,58,237,0.32)", rgb: "124,58,237", mdColor: "deep-purple", mdAccent: "purple", bg: "#0b0816" },
  { name: "Cyan", code: "cyan", accent: "#06b6d4", a2: "#22d3ee", a3: "#67e8f9", glow: "rgba(6,182,212,0.32)", rgb: "6,182,212", mdColor: "cyan", mdAccent: "cyan", bg: "#07111a" },
  { name: "Sky", code: "sky", accent: "#0284c7", a2: "#38bdf8", a3: "#7dd3fc", glow: "rgba(2,132,199,0.32)", rgb: "2,132,199", mdColor: "blue", mdAccent: "light-blue", bg: "#070b1a" },
  { name: "Emerald", code: "emerald", accent: "#059669", a2: "#34d399", a3: "#6ee7b7", glow: "rgba(5,150,105,0.32)", rgb: "5,150,105", mdColor: "green", mdAccent: "green", bg: "#071110" },
  { name: "Rose", code: "rose", accent: "#e11d48", a2: "#fb7185", a3: "#fda4af", glow: "rgba(225,29,72,0.32)", rgb: "225,29,72", mdColor: "pink", mdAccent: "pink", bg: "#14070a" },
  { name: "Amber", code: "amber", accent: "#d97706", a2: "#fbbf24", a3: "#fde68a", glow: "rgba(217,119,6,0.32)", rgb: "217,119,6", mdColor: "orange", mdAccent: "orange", bg: "#120e07" },
  { name: "Lime", code: "lime", accent: "#65a30d", a2: "#a3e635", a3: "#d9f99d", glow: "rgba(101,163,13,0.32)", rgb: "101,163,13", mdColor: "light-green", mdAccent: "lime", bg: "#0d1007" },
  { name: "Crimson", code: "crimson", accent: "#dc2626", a2: "#ef4444", a3: "#f87171", glow: "rgba(220,38,38,0.32)", rgb: "220,38,38", mdColor: "red", mdAccent: "red", bg: "#150808" },
  ];

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16);
  return `${r},${g},${b}`;
}

function applyTheme(theme, save = true) {
  const r = document.documentElement;
  r.style.setProperty("--vtx-accent", theme.accent);
  r.style.setProperty("--vtx-accent-2", theme.a2);
  r.style.setProperty("--vtx-accent-3", theme.a3);
  r.style.setProperty("--vtx-glow", theme.glow);
  r.style.setProperty("--vtx-glow-lg", theme.glow.replace("0.32", "0.13"));
  r.style.setProperty("--vtx-glow-sm", theme.glow.replace("0.32", "0.18"));
  r.style.setProperty("--vtx-accent-rgb", theme.rgb);
  r.style.setProperty("--vtx-bg-theme", theme.bg);
  r.style.setProperty("--md-default-bg-color", theme.bg);

  /* Material properties */
  const body = document.body;
  body.setAttribute("data-md-color-primary", theme.mdColor);
  body.setAttribute("data-md-color-accent", theme.mdAccent);

  /* Update header icon color */
  const toggle = document.querySelector(".vtx-theme-toggle-btn");
  if (toggle) toggle.style.color = theme.accent;

  if (save) { try { localStorage.setItem("vtx-theme", theme.code); } catch (_) { } }
}

function buildThemeDots() {
  let saved; try { saved = localStorage.getItem("vtx-theme") || "violet"; } catch (_) { saved = "violet"; }
  const activeTheme = VTX_THEMES.find(t => t.code === saved) || VTX_THEMES[0];

  /* 1. Clear and Build for any existing containers (like footer or custom areas) */
  document.querySelectorAll(".vtx-theme-switcher, .vtx-theme-row").forEach(container => {
    container.innerHTML = "";

    VTX_THEMES.forEach(theme => {
      const btn = document.createElement("button");
      btn.className = "vtx-theme-dot" + (theme.code === saved ? " active" : "");
      btn.style.background = `linear-gradient(135deg, ${theme.accent}, ${theme.a2})`;
      btn.style.color = theme.accent;
      btn.title = theme.name;
      btn.type = "button";
      btn.addEventListener("click", () => {
        document.querySelectorAll(".vtx-theme-dot").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(`.vtx-theme-dot[title="${theme.name}"]`).forEach(b => b.classList.add("active"));
        applyTheme(theme);
      });
      container.appendChild(btn);
    });
  });

  /* 2. Inject into Sidebar if not already there */
  const nav = document.querySelector(".md-nav--primary > .md-nav__list");
  if (nav && !document.querySelector(".vtx-sidebar-theme")) {
    const item = document.createElement("li");
    item.className = "md-nav__item vtx-sidebar-theme";

    const row = document.createElement("div");
    row.className = "vtx-theme-row sidebar-mode";

    const lbl = document.createElement("span");


    VTX_THEMES.forEach(theme => {
      const btn = document.createElement("button");
      btn.className = "vtx-theme-dot" + (theme.code === saved ? " active" : "");
      btn.style.background = `linear-gradient(135deg, ${theme.accent}, ${theme.a2})`;
      btn.title = theme.name;
      btn.addEventListener("click", () => {
        document.querySelectorAll(".vtx-theme-dot").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(`.vtx-theme-dot[title="${theme.name}"]`).forEach(b => b.classList.add("active"));
        applyTheme(theme);
      });
      row.appendChild(btn);
    });
    item.appendChild(row);
    nav.prepend(item);
  }

  /* 3. Inject into Top Navbar (Header) */
  const headerInner = document.querySelector(".md-header__inner");
  if (headerInner && !document.querySelector(".vtx-header-theme")) {
    const container = document.createElement("div");
    container.className = "vtx-header-theme";

    /* Icon Button */
    const iconBtn = document.createElement("button");
    iconBtn.className = "md-header__button md-icon vtx-theme-toggle-btn";
    iconBtn.title = "Change accent color";
    iconBtn.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="width: 24px; height: 24px;">
      <g stroke="none" stroke-width="0"></g>
      <g stroke-linecap="round" stroke-linejoin="round"></g>
      <g>
        <g data-name="color-palette">
          <rect width="24" height="24" opacity="0"></rect>
          <path d="M19.54 5.08A10.61 10.61 0 0 0 11.91 2a10 10 0 0 0-.05 20 2.58 2.58 0 0 0 2.53-1.89 2.52 2.52 0 0 0-.57-2.28.5.5 0 0 1 .37-.83h1.65A6.15 6.15 0 0 0 22 11.33a8.48 8.48 0 0 0-2.46-6.25zM15.88 15h-1.65a2.49 2.49 0 0 0-1.87 4.15.49.49 0 0 1 .12.49c-.05.21-.28.34-.59.36a8 8 0 0 1-7.82-9.11A8.1 8.1 0 0 1 11.92 4H12a8.47 8.47 0 0 1 6.1 2.48 6.5 6.5 0 0 1 1.9 4.77A4.17 4.17 0 0 1 15.88 15z" fill="currentColor"></path>
          <circle cx="12" cy="6.5" r="1.5" fill="currentColor"></circle>
          <path d="M15.25 7.2a1.5 1.5 0 1 0 2.05.55 1.5 1.5 0 0 0-2.05-.55z" fill="currentColor"></path>
          <path d="M8.75 7.2a1.5 1.5 0 1 0 .55 2.05 1.5 1.5 0 0 0-.55-2.05z" fill="currentColor"></path>
          <path d="M6.16 11.26a1.5 1.5 0 1 0 2.08.4 1.49 1.49 0 0 0-2.08-.4z" fill="currentColor"></path>
        </g>
      </g>
    </svg>`;

    /* Dropdown */
    const dropdown = document.createElement("div");
    dropdown.className = "vtx-header-theme-dropdown";

    const row = document.createElement("div");
    row.className = "vtx-theme-row header-mode";

    VTX_THEMES.forEach(theme => {
      const btn = document.createElement("button");
      btn.className = "vtx-theme-dot" + (theme.code === saved ? " active" : "");
      btn.style.background = `linear-gradient(135deg, ${theme.accent}, ${theme.a2})`;
      btn.title = theme.name;
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        document.querySelectorAll(".vtx-theme-dot").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(`.vtx-theme-dot[title="${theme.name}"]`).forEach(b => b.classList.add("active"));
        applyTheme(theme);
        dropdown.classList.remove("open");
      });
      row.appendChild(btn);
    });

    dropdown.appendChild(row);
    container.appendChild(iconBtn);
    container.appendChild(dropdown);

    iconBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      dropdown.classList.toggle("open");
    });

    document.addEventListener("click", () => dropdown.classList.remove("open"));

    const target = headerInner.querySelector(".md-header__source") || headerInner.querySelector(".md-search");
    if (target) headerInner.insertBefore(container, target);
    else headerInner.appendChild(container);
  }

  applyTheme(activeTheme, false);
}

/* ══════════════════════════════════════════════════════════════════
   PARTICLE CANVAS
   ══════════════════════════════════════════════════════════════════ */
function initParticles() {
  const canvas = document.querySelector(".vtx-particle-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  let W, H, particles = [], raf;

  function resize() {
    W = canvas.width = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }

  function Particle() {
    this.reset = function () {
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.vx = (Math.random() - 0.5) * 0.35;
      this.vy = (Math.random() - 0.5) * 0.35;
      this.r = Math.random() * 1.8 + 0.6;
      this.a = Math.random() * 0.55 + 0.12;
    };
    this.reset();
  }

  function getAccentRgb() {
    const v = getComputedStyle(document.documentElement).getPropertyValue("--vtx-accent-rgb").trim() || "124,58,237";
    return v;
  }

  /* Reduce particle count on smaller screens for better performance */
  function getParticleCount() {
    const w = window.innerWidth;
    if (w < 480) return 25;
    if (w < 768) return 45;
    return 80;
  }

  function build(n) {
    n = (n !== undefined) ? n : getParticleCount();
    particles = [];
    for (let i = 0; i < n; i++) particles.push(new Particle());
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    const rgb = getAccentRgb();
    particles.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < 0 || p.x > W) p.vx *= -1;
      if (p.y < 0 || p.y > H) p.vy *= -1;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${rgb},${p.a})`;
      ctx.fill();
    });

    /* Draw connections */
    const maxDist = 100;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < maxDist) {
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          const a = (1 - d / maxDist) * 0.12;
          ctx.strokeStyle = `rgba(${rgb},${a})`;
          ctx.lineWidth = 0.6;
          ctx.stroke();
        }
      }
    }
    raf = requestAnimationFrame(draw);
  }

  resize();
  build();
  draw();

  /* Rebuild with correct count on orientation/resize */
  const ro = new ResizeObserver(() => { resize(); build(getParticleCount()); });
  ro.observe(canvas);

  /* Stop when hero is not visible */
  const io = new IntersectionObserver(entries => {
    if (!entries[0].isIntersecting) { cancelAnimationFrame(raf); }
    else draw();
  }, { threshold: 0.01 });
  io.observe(canvas);
}

/* ══════════════════════════════════════════════════════════════════
   ORB PARALLAX (subtle mouse tracking)
   ══════════════════════════════════════════════════════════════════ */
function initOrbParallax() {
  /* Skip mouse parallax on touch / pointer-coarse devices (phones/tablets) */
  if (window.matchMedia("(pointer: coarse)").matches) return;

  const wrapper = document.querySelector(".vtx-hero-wrapper");
  if (!wrapper) return;
  const orbs = wrapper.querySelectorAll(".vtx-orb");
  if (!orbs.length) return;

  let tX = 0, tY = 0, cX = 0, cY = 0;
  const speeds = [0.018, -0.012, 0.025];

  wrapper.addEventListener("mousemove", e => {
    const rect = wrapper.getBoundingClientRect();
    tX = (e.clientX - rect.left - rect.width / 2) * 0.5;
    tY = (e.clientY - rect.top - rect.height / 2) * 0.5;
  });

  let af;
  function tick() {
    cX += (tX - cX) * 0.04;
    cY += (tY - cY) * 0.04;
    orbs.forEach((orb, i) => {
      const s = speeds[i] || 0.02;
      orb.style.transform = `translate(${cX * s * 100}px, ${cY * s * 100}px)`;
    });
    af = requestAnimationFrame(tick);
  }
  tick();
}

/* ══════════════════════════════════════════════════════════════════
   SCROLL REVEAL
   ══════════════════════════════════════════════════════════════════ */
function initScrollReveal() {
  const els = document.querySelectorAll(".vtx-reveal");
  if (!els.length) return;
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add("vtx-revealed");
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12 });
  els.forEach(el => io.observe(el));
}

/* ══════════════════════════════════════════════════════════════════
   STAT COUNTER ANIMATION
   ══════════════════════════════════════════════════════════════════ */
function animateCounters() {
  document.querySelectorAll("[data-target]").forEach(el => {
    const target = parseFloat(el.getAttribute("data-target"));
    const suffix = el.getAttribute("data-suffix") || "";
    const prefix = el.getAttribute("data-prefix") || "";
    const decimals = target % 1 !== 0 ? 1 : 0;
    const dur = 1100;
    const start = performance.now();

    (function tick(now) {
      const p = Math.min((now - start) / dur, 1);
      const e = 1 - Math.pow(1 - p, 3);
      const v = (e * target).toFixed(decimals);
      el.textContent = prefix + parseFloat(v).toLocaleString() + suffix;
      if (p < 1) requestAnimationFrame(tick);
    })(start);
  });
}

/**
 * Flawless custom scroll spy and sidebar scroll centering.
 * Completely overrides Material's native buggy observer.
 */
function initSidebarAutoScroll() {
  const sidebarWrap = document.querySelector(".md-sidebar--primary .md-sidebar__scrollwrap");
  const primaryLinks = Array.from(document.querySelectorAll(".md-sidebar--primary .md-nav__link"));
  const secondaryLinks = Array.from(document.querySelectorAll(".md-sidebar--secondary .md-nav__link"));
  const headings = Array.from(document.querySelectorAll(".md-content h1[id], .md-content h2[id], .md-content h3[id], .md-content h4[id], .md-content h5[id], .md-content h6[id]"));

  if (!sidebarWrap || (primaryLinks.length === 0 && secondaryLinks.length === 0)) return;

  globalThis._vtxSpyDom = { sidebarWrap, primaryLinks, secondaryLinks, headings };

  const getActiveId = () => {
    if (headings.length === 0) return "";
    const trig = window.innerHeight * 0.4;
    let closest = headings[0];
    for (const h of headings) {
      if (h.getBoundingClientRect().top <= trig) closest = h;
      else break;
    }
    return closest.id;
  };

  const matchLink = (links, path, hash, matchHash = true) => {
    return links.find(el => {
      try {
        const u = new URL(el.href);
        const lp = u.pathname.replace(/\/$/, "") || "/";
        return lp === path && (!matchHash || u.hash === hash);
      } catch { return false; }
    });
  };

  if (globalThis._vtxSpySync) globalThis._vtxSpySync();

  if (!globalThis._vtxCustomSpyBound) {
    globalThis._vtxSpySync = () => {
      const dom = globalThis._vtxSpyDom;
      if (!dom) return;

      const activeId = getActiveId();
      const path = window.location.pathname.replace(/\/$/, "") || "/";
      const hash = activeId ? `#${activeId}` : (window.location.hash || "");

      dom.primaryLinks.forEach(el => el.classList.remove("vtx-sidebar-active"));
      dom.secondaryLinks.forEach(el => el.classList.remove("vtx-sidebar-active"));

      const pMatch = matchLink(dom.primaryLinks, path, hash) || matchLink(dom.primaryLinks, path, hash, false);
      if (pMatch) pMatch.classList.add("vtx-sidebar-active");

      const sMatch = dom.secondaryLinks.find(el => {
        try { return new URL(el.href).hash === hash; } catch { return false; }
      });
      if (sMatch) sMatch.classList.add("vtx-sidebar-active");

      if (pMatch && dom.sidebarWrap) {
        const isBottom = (window.innerHeight + window.pageYOffset) >= (document.body.offsetHeight - 80);
        const isTop = window.pageYOffset < 50;

        if (isTop) dom.sidebarWrap.scrollTo({ top: 0, behavior: "auto" });
        else if (isBottom) dom.sidebarWrap.scrollTo({ top: dom.sidebarWrap.scrollHeight, behavior: "auto" });
        else {
          const aRect = pMatch.getBoundingClientRect(), wRect = dom.sidebarWrap.getBoundingClientRect();
          const tGuard = (document.querySelector(".md-header")?.offsetHeight ?? 0) + (document.querySelector(".md-tabs")?.offsetHeight ?? 0);
          dom.sidebarWrap.scrollTo({ top: dom.sidebarWrap.scrollTop + (aRect.top - wRect.top) - tGuard - 16, behavior: "auto" });
        }
      }
    };

    let ticking = false;
    window.addEventListener("scroll", () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          if (globalThis._vtxSpySync) globalThis._vtxSpySync();
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });

    globalThis._vtxCustomSpyBound = true;
  }

  // Ensure initial sync completes fully after rendering layout shifts
  setTimeout(() => globalThis._vtxSpySync && globalThis._vtxSpySync(), 50);
  setTimeout(() => globalThis._vtxSpySync && globalThis._vtxSpySync(), 200);
}

/**
 * Relocates the footer navigation links into the content area.
 * This ensures they appear "at the end of the section" and not below the sidebars.
 */
function relocateFooterNav() {
  const footerNav = document.querySelector(".md-footer__inner");
  const contentInner = document.querySelector(".md-content__inner");

  if (footerNav && contentInner) {
    if (document.querySelector(".vtx-hero-wrapper")) return;
    if (contentInner.querySelector(".vtx-footer-nav-container")) return;

    const wrapper = document.createElement("div");
    wrapper.className = "vtx-footer-nav-container";
    wrapper.appendChild(footerNav);
    contentInner.appendChild(wrapper);
  }
}

function observeStats() {
  const bar = document.querySelector(".vtx-stats-bar");
  if (!bar) return;
  const io = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) { animateCounters(); io.disconnect(); }
  }, { threshold: 0.4 });
  io.observe(bar);
}

/* ══════════════════════════════════════════════════════════════════
   HERO ENTRANCE DELAY SEQUENCING
   ══════════════════════════════════════════════════════════════════ */
function sequenceEntrance() {
  const el = document.querySelectorAll(".vtx-animate-in");
  el.forEach((e, i) => { e.style.animationDelay = `${i * 80}ms`; });
}

/* ══════════════════════════════════════════════════════════════════
   COPY BUTTON VISUAL FEEDBACK
   ══════════════════════════════════════════════════════════════════ */
function initCopyFeedback() {
  document.querySelectorAll(".md-clipboard").forEach(btn => {
    btn.addEventListener("click", () => {
      btn.style.color = "#10b981";
      btn.style.transform = "scale(0.86)";
      setTimeout(() => { btn.style.color = ""; btn.style.transform = ""; }, 1100);
    });
  });
}

/* ══════════════════════════════════════════════════════════════════
   HEADER SHADOW ON SCROLL
   ══════════════════════════════════════════════════════════════════ */
function initHeaderScroll() {
  const header = document.querySelector(".md-header");
  if (!header) return;
  let ticking = false;
  window.addEventListener("scroll", () => {
    if (!ticking) {
      requestAnimationFrame(() => {
        header[window.scrollY > 8 ? "setAttribute" : "removeAttribute"]("data-md-state", window.scrollY > 8 ? "shadow" : "");
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
}

/* ── Search Highlight Clear ───────────────────────────────────── */
function initSearchAutoClear() {
  const input = document.querySelector(".md-search__input");
  if (!input) return;

  const clearHighlights = () => {
    const url = new URL(window.location.href);
    if (url.searchParams.has("h")) {
      url.searchParams.delete("h");
      window.history.replaceState({}, "", url.toString());

      /* Force remove mark tags if Material doesn't */
      document.querySelectorAll("mark").forEach(m => {
        const t = document.createTextNode(m.textContent);
        m.parentNode.replaceChild(t, m);
      });
    }
  };

  input.addEventListener("input", () => {
    if (!input.value.trim()) clearHighlights();
  });

  /* Also handle the 'X' button or Esc key */
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setTimeout(clearHighlights, 100);
  });

  /* Observer for the reset button which Material injects */
  const reset = document.querySelector(".md-search__icon[for='__search'] + .md-search__icon");
  if (reset) reset.addEventListener("click", () => setTimeout(clearHighlights, 100));
}

/* ══════════════════════════════════════════════════════════════════
   MAIN INIT
   ══════════════════════════════════════════════════════════════════ */
/* ── Dynamic Brand Logo ───────────────────────────────────────── */
function injectDynamicLogo() {
  const logoLink = document.querySelector(".md-logo");
  if (!logoLink) return;

  /* Remove old img if present */
  const oldImg = logoLink.querySelector("img");
  if (oldImg) oldImg.remove();

  if (logoLink.querySelector(".vtx-dynamic-logo")) return;

  const svgHtml = `
  <svg class="vtx-dynamic-logo space-logo" viewBox="0 0 876 667" fill="none" xmlns="http://www.w3.org/2000/svg">
    <style>
      @keyframes vtx-star-twinkle {
        0%,100%{ opacity:0.25; }
        50%    { opacity:1; }
      }
      @keyframes vtx-data-stream {
        0%   { stroke-dashoffset: 350; opacity:0; }
        20%  { opacity: 0.7; }
        80%  { opacity: 0.7; }
        100% { stroke-dashoffset: 0; opacity: 0; }
      }
      @keyframes vtx-logo-chromatic {
        0%,100% { transform: translate(0,0); }
        25%     { transform: translate(1.4px,0); }
        75%     { transform: translate(-1.4px,0); }
      }
      @keyframes vtx-logo-shimmer-move {
        from { transform: translateX(-150%); }
        to { transform: translateX(150%); }
      }

      .vtx-dynamic-logo {
        display: block;
        width: 100% !important;
        height: auto !important;
        pointer-events: none;
      }

      .vtx-shimmer-rect {
        animation: vtx-logo-shimmer-move 4s linear infinite;
      }
    </style>
    <defs>
      <linearGradient id="vtx-s1" x1="52" y1="51" x2="876" y2="667" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="var(--vtx-accent-2)" stop-opacity="0.4"/>
        <stop offset="35%" stop-color="var(--vtx-accent)"/>
        <stop offset="70%" stop-color="var(--vtx-accent-2)"/>
        <stop offset="100%" stop-color="var(--vtx-accent-3)"/>
      </linearGradient>
      <linearGradient id="vtx-s2" x1="824" y1="52" x2="100" y2="600" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="var(--vtx-accent-2)"/>
        <stop offset="40%" stop-color="var(--vtx-accent)"/>
        <stop offset="100%" stop-color="var(--vtx-accent-3)"/>
      </linearGradient>
      <linearGradient id="vtx-s3" x1="438" y1="51" x2="300" y2="608" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stop-color="rgba(var(--vtx-accent-rgb), 0.5)"/>
        <stop offset="50%" stop-color="var(--vtx-accent)"/>
        <stop offset="100%" stop-color="var(--vtx-accent-3)"/>
      </linearGradient>

      <linearGradient id="vtx-logo-shimmer-grad" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="white" stop-opacity="0"/>
        <stop offset="50%" stop-color="white" stop-opacity="0.65"/>
        <stop offset="100%" stop-color="white" stop-opacity="0"/>
      </linearGradient>

    <clipPath id="vtx-logo-clip">
        <path d="M285.83 294.944L438.33 607.944L588.33 296.944L720.83 198.944L689.33 262.944L743.526 212.039C788.259 170.023 816.553 113.44 823.33 52.444L758.83 110.444L721.369 144.13C703.367 160.318 684.213 175.177 664.058 188.59L552.33 262.944L437.83 501.444L320.83 262.944L213.83 188.444L111.83 107.444L52.8304 51.444L54.9501 65.7162C63.2899 121.871 90.42 173.54 131.911 212.288L188.83 265.444L155.83 200.944L285.83 294.944Z"/>
        <path d="M306.107 156.52L436.927 429.062C437.291 429.819 438.369 429.818 438.731 429.061L569.059 156.513C569.225 156.165 569.576 155.944 569.961 155.944H602.761C603.492 155.944 603.976 156.704 603.667 157.367L569.83 229.944L644.609 176.602C644.754 176.499 644.869 176.358 644.941 176.196L673.905 111.352C674.201 110.69 673.717 109.944 672.992 109.944H541.457C541.074 109.944 540.724 110.163 540.557 110.508L438.237 321.574C437.871 322.328 436.796 322.325 436.435 321.569L335.602 110.513C335.436 110.165 335.085 109.944 334.7 109.944H200.921C200.184 109.944 199.701 110.713 200.02 111.377L230.721 175.217C230.793 175.366 230.901 175.495 231.034 175.592L305.83 229.944L269.549 157.872C269.217 157.212 269.69 156.432 270.429 156.422L305.192 155.953C305.581 155.947 305.938 156.169 306.107 156.52Z"/>
        <path d="M364.83 505.444L271.83 309.444L219.83 273.944L258.83 346.944L200.954 312.776C184.238 302.908 168.441 291.562 153.751 278.875L98.8304 231.444L104.162 246.702C128.308 315.812 182.325 370.353 251.199 395.166L290.83 409.444L364.83 505.444Z"/>
        <path d="M511.83 505.444L604.83 309.444L656.83 273.944L617.83 346.944L675.707 312.776C692.422 302.908 708.22 291.562 722.91 278.875L777.83 231.444L772.499 246.702C748.352 315.812 694.336 370.353 625.462 395.166L585.83 409.444L511.83 505.444Z"/>
    </clipPath>
    </defs>

    <!-- Stars -->
    <circle cx="120" cy="80" r="1.5" fill="var(--vtx-accent-2)" style="animation:vtx-star-twinkle 2.1s ease-in-out infinite;"/>
    <circle cx="750" cy="60" r="1.2" fill="var(--vtx-accent)" style="animation:vtx-star-twinkle 3s ease-in-out infinite 0.5s;"/>
    <circle cx="820" cy="180" r="2" fill="var(--vtx-accent-3)" style="animation:vtx-star-twinkle 1.8s ease-in-out infinite 1s;"/>
    <circle cx="60" cy="400" r="1.5" fill="var(--vtx-accent)" style="animation:vtx-star-twinkle 2.5s ease-in-out infinite 0.3s;"/>
    <circle cx="830" cy="500" r="1" fill="var(--vtx-accent-2)" style="animation:vtx-star-twinkle 3.2s ease-in-out infinite 0.8s;"/>
    <circle cx="400" cy="30" r="1" fill="white" style="animation:vtx-star-twinkle 3.5s ease-in-out infinite 0.2s;"/>
    <ellipse cx="438" cy="334" rx="370" ry="90" stroke="var(--vtx-accent)" stroke-width="0.7" fill="none" opacity="0.25" transform="rotate(-20,438,334)"/>

    <!-- The Orbiting Planet/Orb -->
    <circle r="4" fill="var(--vtx-accent-2)" opacity="0.8" style="animation:vtx-star-twinkle 1s linear infinite;">
      <animateMotion dur="12s" repeatCount="indefinite">
        <mpath href="#vtx-orbit-path"/>
      </animateMotion>
    </circle>
    <path id="vtx-orbit-path" d="M 68 334 A 370 90 0 1 1 808 334 A 370 90 0 1 1 68 334" transform="rotate(-20,438,334)" fill="none"/>

    <!-- Chromatic Aberration Under-layer -->
    <g style="animation:vtx-logo-chromatic 0.2s ease-in-out infinite;" opacity="0.3">
      <path d="M285.83 294.944L438.33 607.944L588.33 296.944L720.83 198.944L689.33 262.944L743.526 212.039C788.259 170.023 816.553 113.44 823.33 52.444L758.83 110.444L721.369 144.13C703.367 160.318 684.213 175.177 664.058 188.59L552.33 262.944L437.83 501.444L320.83 262.944L213.83 188.444L111.83 107.444L52.8304 51.444L54.9501 65.7162C63.2899 121.871 90.42 173.54 131.911 212.288L188.83 265.444L155.83 200.944L285.83 294.944Z" fill="var(--vtx-accent-2)"/>
    </g>

    <!-- Main Logo Paths -->
    <path d="M285.83 294.944L438.33 607.944L588.33 296.944L720.83 198.944L689.33 262.944L743.526 212.039C788.259 170.023 816.553 113.44 823.33 52.444L758.83 110.444L721.369 144.13C703.367 160.318 684.213 175.177 664.058 188.59L552.33 262.944L437.83 501.444L320.83 262.944L213.83 188.444L111.83 107.444L52.8304 51.444L54.9501 65.7162C63.2899 121.871 90.42 173.54 131.911 212.288L188.83 265.444L155.83 200.944L285.83 294.944Z" fill="url(#vtx-s1)" opacity="0.95"/>
    <path d="M306.107 156.52L436.927 429.062C437.291 429.819 438.369 429.818 438.731 429.061L569.059 156.513C569.225 156.165 569.576 155.944 569.961 155.944H602.761C603.492 155.944 603.976 156.704 603.667 157.367L569.83 229.944L644.609 176.602C644.754 176.499 644.869 176.358 644.941 176.196L673.905 111.352C674.201 110.69 673.717 109.944 672.992 109.944H541.457C541.074 109.944 540.724 110.163 540.557 110.508L438.237 321.574C437.871 322.328 436.796 322.325 436.435 321.569L335.602 110.513C335.436 110.165 335.085 109.944 334.7 109.944H200.921C200.184 109.944 199.701 110.713 200.02 111.377L230.721 175.217C230.793 175.366 230.901 175.495 231.034 175.592L305.83 229.944L269.549 157.872C269.217 157.212 269.69 156.432 270.429 156.422L305.192 155.953C305.581 155.947 305.938 156.169 306.107 156.52Z" fill="url(#vtx-s2)" opacity="0.95"/>

    <!-- Data Stream Outlines -->
    <path d="M285.83 294.944L438.33 607.944L588.33 296.944L720.83 198.944L689.33 262.944L743.526 212.039C788.259 170.023 816.553 113.44 823.33 52.444L758.83 110.444L721.369 144.13C703.367 160.318 684.213 175.177 664.058 188.59L552.33 262.944L437.83 501.444L320.83 262.944L213.83 188.444L111.83 107.444L52.8304 51.444L54.9501 65.7162C63.2899 121.871 90.42 173.54 131.911 212.288L188.83 265.444L155.83 200.944L285.83 294.944Z" fill="none" stroke="var(--vtx-accent-2)" stroke-width="2.5" stroke-dasharray="200 400" style="animation:vtx-data-stream 6s ease-in-out infinite;"/>
    <path d="M306.107 156.52L436.927 429.062C437.291 429.819 438.369 429.818 438.731 429.061L569.059 156.513C569.225 156.165 569.576 155.944 569.961 155.944H602.761C603.492 155.944 603.976 156.704 603.667 157.367L569.83 229.944L644.609 176.602C644.754 176.499 644.869 176.358 644.941 176.196L673.905 111.352C674.201 110.69 673.717 109.944 672.992 109.944H541.457C541.074 109.944 540.724 110.163 540.557 110.508L438.237 321.574C437.871 322.328 436.796 322.325 436.435 321.569L335.602 110.513C335.436 110.165 335.085 109.944 334.7 109.944H200.921C200.184 109.944 199.701 110.713 200.02 111.377L230.721 175.217C230.793 175.366 230.901 175.495 231.034 175.592L305.83 229.944L269.549 157.872C269.217 157.212 269.69 156.432 270.429 156.422L305.192 155.953C305.581 155.947 305.938 156.169 306.107 156.52Z" fill="none" stroke="white" stroke-width="2" stroke-dasharray="150 600" style="animation:vtx-data-stream 8s ease-in-out infinite 2s;"/>

    <!-- Theme-Dynamic Wings -->
    <path d="M364.83 505.444L271.83 309.444L219.83 273.944L258.83 346.944L200.954 312.776C184.238 302.908 168.441 291.562 153.751 278.875L98.8304 231.444L104.162 246.702C128.308 315.812 182.325 370.353 251.199 395.166L290.83 409.444L364.83 505.444Z" fill="url(#vtx-s3)" opacity="0.92"/>
    <path d="M511.83 505.444L604.83 309.444L656.83 273.944L617.83 346.944L675.707 312.776C692.422 302.908 708.22 291.562 722.91 278.875L777.83 231.444L772.499 246.702C748.352 315.812 694.336 370.353 625.462 395.166L585.83 409.444L511.83 505.444Z" fill="url(#vtx-s3)" opacity="0.92"/>

    <!-- Shimmer Top-Layer (Clipped) -->
    <g clip-path="url(#vtx-logo-clip)">
      <rect x="-100" y="-100" width="1200" height="900" fill="url(#vtx-logo-shimmer-grad)" class="vtx-shimmer-rect" opacity="0.65"/>
    </g>
  </svg>
  `;

  logoLink.innerHTML = svgHtml;
}

/* ══════════════════════════════════════════════════════════════════
   SIDEBAR SCROLL RESET
   Reset sidebar to top on every page navigation so the active item
   is always visible from the start.
   ══════════════════════════════════════════════════════════════════ */
function resetSidebarScroll() {
  document.querySelectorAll('.md-sidebar__scrollwrap').forEach(sw => {
    sw.scrollTop = 0;
  });
}

/* ══════════════════════════════════════════════════════════════
   RESPONSIVE TABLE WRAPPER
   Wraps every plain Markdown table in a .vtx-table-wrap div so the
   table element itself keeps display:table layout while the wrapper
   provides overflow-x:auto scrolling and border-radius clipping.
   Re-running is safe — already-wrapped tables are skipped.
   ══════════════════════════════════════════════════════════════ */
function wrapTables() {
  document.querySelectorAll(".md-typeset table:not([class])").forEach(table => {
    if (table.parentElement && table.parentElement.classList.contains("vtx-table-wrap")) return;
    const wrap = document.createElement("div");
    wrap.className = "vtx-table-wrap";
    table.parentNode.insertBefore(wrap, table);
    wrap.appendChild(table);
  });
}

function init() {
  const isHome = !!document.querySelector(".vtx-hero-wrapper") || 
                 window.location.pathname === "/" || 
                 window.location.pathname.endsWith("/index.html") ||
                 window.location.pathname.endsWith("/");
  
  if (isHome) {
    document.body.classList.add("vtx-is-home");
  }
  resetSidebarScroll();
  wrapTables();
  injectDynamicLogo();
  buildThemeDots();
  initParticles();
  initOrbParallax();
  initScrollReveal();
  observeStats();
  sequenceEntrance();
  initCopyFeedback();
  initHeaderScroll();
  initSearchAutoClear();
  relocateFooterNav();
  initSidebarAutoScroll();
}

/* Bootstrap — single subscription handles both first load and instant navigation */
if (typeof document$ !== "undefined") {
  document$.subscribe(() => {
    init();
  });
} else {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
}
