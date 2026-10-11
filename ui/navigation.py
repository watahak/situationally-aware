from __future__ import annotations

import streamlit as st

from ui.theme import _css_theme, get_active_palette


_TOC_COMPONENT = st.components.v2.component(
    "mini_quant_sidebar_toc",
    html="""
<div data-role="toc-shell">
  <div data-role="toc-title">On This Page</div>
  <nav data-role="toc-nav" aria-label="On this page"></nav>
</div>
<style>
  [data-role="toc-shell"] {
    padding: 0.5rem 0.25rem;
  }
  [data-role="toc-title"] {
    color: var(--toc-muted);
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
    padding-left: 0.5rem;
  }
  [data-role="toc-nav"] {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
  }
  .mq-toc-link {
    display: block;
    border-left: 2px solid transparent;
    color: var(--toc-text);
    font-size: 0.8rem;
    line-height: 1.35;
    text-decoration: none;
    padding: 0.3rem 0.5rem;
    border-radius: 0.3rem;
    cursor: pointer;
    transition: border-color 150ms, color 150ms, background 150ms;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .mq-toc-link:hover {
    color: var(--toc-strong);
    background: var(--toc-hover-bg);
  }
  .mq-toc-link[data-active="true"] {
    color: var(--toc-strong);
    border-left-color: var(--toc-accent);
    background: var(--toc-active-bg);
  }
  .mq-toc-empty {
    color: var(--toc-muted);
    font-size: 0.78rem;
    padding: 0.2rem 0.5rem;
    font-style: italic;
  }
</style>
""",
    js="""
const instances =
  window.__mqTocInstances || (window.__mqTocInstances = new WeakMap());

function slugify(text) {
  return "toc-" + text.toLowerCase()
    .replace(/[^a-z0-9\\s-]/g, "")
    .trim()
    .replace(/\\s+/g, "-")
    .replace(/-+/g, "-");
}

function autoHeight(parentElement, shell) {
  const h = shell.getBoundingClientRect().height;
  let el = parentElement;
  for (let i = 0; i < 8 && el; i++) {
    if (el.style) {
      el.style.height = h ? (h + "px") : "auto";
      el.style.overflow = "visible";
    }
    if (el.getAttribute && el.getAttribute("data-testid") === "stSidebar") break;
    el = el.parentElement || el.host;
  }
}

export default function (component) {
  const { parentElement, data } = component;
  if (!parentElement) return;

  const shell = parentElement.querySelector('[data-role="toc-shell"]');
  const nav = parentElement.querySelector('[data-role="toc-nav"]');
  if (!shell || !nav) return;

  // Apply theme CSS variables
  const vars = {
    "--toc-muted": data?.tocMuted || "#94A3B8",
    "--toc-text": data?.tocText || "#B5C4D9",
    "--toc-strong": data?.tocStrong || "#E2E8F0",
    "--toc-accent": data?.tocAccent || "#38BDF8",
    "--toc-hover-bg": data?.tocHoverBg || "rgba(56,189,248,0.08)",
    "--toc-active-bg": data?.tocActiveBg || "rgba(56,189,248,0.12)",
  };
  for (const [k, v] of Object.entries(vars)) shell.style.setProperty(k, v);

  let state = instances.get(parentElement);
  if (!state) {
    state = { cleanup: null, activeId: null };
    instances.set(parentElement, state);
  }
  if (state.cleanup) state.cleanup();

  const teardowns = [];
  state.activeId = null;

  function getActivePanel() {
    const tabs = document.querySelectorAll('button[role="tab"]');
    let idx = -1;
    tabs.forEach((t, i) => {
      if (t.getAttribute("aria-selected") === "true") idx = i;
    });
    if (idx < 0) idx = 0;
    const panels = document.querySelectorAll('div[role="tabpanel"]');
    return panels[idx] || null;
  }

  function setActive(id) {
    if (state.activeId === id) return;
    state.activeId = id;
    nav.querySelectorAll(".mq-toc-link").forEach(link => {
      link.setAttribute("data-active", link.dataset.targetId === id ? "true" : "false");
    });
  }

  function buildTOC() {
    nav.innerHTML = "";
    state.activeId = null;

    const panel = getActivePanel();
    if (!panel) {
      nav.innerHTML = '<div class="mq-toc-empty">Loading…</div>';
      autoHeight(parentElement, shell);
      return;
    }

    const headings = Array.from(panel.querySelectorAll("h2")).filter(h => {
      const text = (h.textContent || "").trim();
      if (!text) return false;
      if (h.closest("[data-testid='stExpander']")) return false;
      return true;
    });

    if (!headings.length) {
      nav.innerHTML = '<div class="mq-toc-empty">No sections on this tab.</div>';
      autoHeight(parentElement, shell);
      return;
    }

    const usedIds = new Set();
    const fragment = document.createDocumentFragment();

    headings.forEach(h => {
      const text = (h.textContent || "").trim();
      let id = h.id || slugify(text);
      while (usedIds.has(id)) id += "-2";
      usedIds.add(id);
      if (!h.id) h.id = id;

      const link = document.createElement("a");
      link.className = "mq-toc-link";
      link.textContent = text;
      link.title = text;
      link.dataset.targetId = id;
      link.href = "#" + id;
      link.addEventListener("click", e => {
        e.preventDefault();
        h.scrollIntoView({ behavior: "smooth", block: "start" });
        setTimeout(() => setActive(id), 350);
      });
      fragment.appendChild(link);
    });

    nav.appendChild(fragment);
    autoHeight(parentElement, shell);

    // Scroll-spy via IntersectionObserver
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting && entry.target.id) {
          setActive(entry.target.id);
          break;
        }
      }
    }, { rootMargin: "-5% 0px -85% 0px", threshold: 0 });

    headings.forEach(h => observer.observe(h));
    teardowns.push(() => observer.disconnect());

    // Fallback: pick the nearest heading on scroll
    const onScroll = () => {
      const threshold = window.innerHeight * 0.25;
      let best = null;
      for (const h of headings) {
        if (h.getBoundingClientRect().top <= threshold) best = h;
      }
      if (!best) best = headings.find(h => h.getBoundingClientRect().top > 0) || headings[0];
      if (best && best.id) setActive(best.id);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    teardowns.push(() => window.removeEventListener("scroll", onScroll));

    // Set initial active
    onScroll();
  }

  // Debounced rebuild
  let rebuildTimer = null;
  function scheduleRebuild() {
    if (rebuildTimer) clearTimeout(rebuildTimer);
    rebuildTimer = setTimeout(() => { rebuildTimer = null; buildTOC(); }, 60);
  }

  // Build immediately
  buildTOC();

  // Watch for tab switches
  const tablist = document.querySelector('[role="tablist"]');
  if (tablist) {
    const tabObs = new MutationObserver(scheduleRebuild);
    tabObs.observe(tablist, { attributes: true, subtree: true, attributeFilter: ["aria-selected"] });
    teardowns.push(() => tabObs.disconnect());
  }

  // Watch for content changes in the main area (new headings appearing)
  const main = document.querySelector('[data-testid="stMain"]');
  if (main) {
    const mainObs = new MutationObserver(scheduleRebuild);
    mainObs.observe(main, { childList: true, subtree: true });
    teardowns.push(() => mainObs.disconnect());
  }

  // Cleanup
  state.cleanup = () => {
    while (teardowns.length) { try { teardowns.pop()(); } catch (_) {} }
    if (rebuildTimer) { clearTimeout(rebuildTimer); rebuildTimer = null; }
  };

  return () => {
    if (state.cleanup) state.cleanup();
    instances.delete(parentElement);
  };
}
""",
)


def render_toc(theme_mode: str) -> None:
    """Render a sidebar table of contents for active tab headings."""
    mode = theme_mode if theme_mode in {"light", "dark"} else "dark"
    css_theme = _css_theme(mode)
    palette = get_active_palette(mode)

    _TOC_COMPONENT(
        key="mini-quant-sidebar-toc",
        data={
            "tocMuted": css_theme["sidebar_muted"],
            "tocText": css_theme["sidebar_caption"],
            "tocStrong": css_theme["body_strong"],
            "tocAccent": palette["accent"],
            "tocHoverBg": css_theme["sidebar_radio_bg"],
            "tocActiveBg": palette["accent_fill"],
        },
        width="stretch",
        height=48,
    )


_BACK_TO_TOP = st.components.v2.component(
    "mini_quant_back_to_top",
    html="""
<div data-role="btt-wrap">
  <button type="button" data-role="btt-btn">&#8593; Back to top</button>
</div>
<style>
  [data-role="btt-wrap"] {
    display: flex;
    justify-content: center;
    padding: 1.2rem 0 0.4rem;
  }
  [data-role="btt-btn"] {
    border: 1px solid var(--btt-border);
    background: var(--btt-bg);
    color: var(--btt-text);
    border-radius: 999px;
    font-size: 0.82rem;
    font-weight: 600;
    padding: 0.5rem 1.2rem;
    cursor: pointer;
    transition: border-color 140ms, background 140ms;
  }
  [data-role="btt-btn"]:hover {
    border-color: var(--btt-accent);
    background: var(--btt-hover);
  }
</style>
""",
    js="""
export default function (component) {
  const { parentElement, data } = component;
  if (!parentElement || !data) return;

  const wrap = parentElement.querySelector('[data-role="btt-wrap"]');
  const btn = parentElement.querySelector('[data-role="btt-btn"]');
  if (!wrap || !btn) return;

  wrap.style.setProperty("--btt-border", data.borderColor || "transparent");
  wrap.style.setProperty("--btt-bg", data.bgColor || "transparent");
  wrap.style.setProperty("--btt-hover", data.hoverColor || "transparent");
  wrap.style.setProperty("--btt-text", data.textColor || "#E2E8F0");
  wrap.style.setProperty("--btt-accent", data.accentColor || "#38BDF8");

  btn.onclick = () => {
    let el = document.querySelector('[data-testid="stMainBlockContainer"]');
    while (el) {
      const ov = getComputedStyle(el).overflowY;
      if ((ov === "auto" || ov === "scroll") && el.scrollHeight > el.clientHeight) {
        el.scrollTo({ top: 0, behavior: "smooth" });
        return;
      }
      el = el.parentElement;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
}
""",
)


def render_back_to_top(theme_mode: str, *, key: str) -> None:
    mode = theme_mode if theme_mode in {"light", "dark"} else "dark"
    css_theme = _css_theme(mode)
    palette = get_active_palette(mode)

    _BACK_TO_TOP(
        key=key,
        data={
            "borderColor": css_theme["card_border"],
            "bgColor": css_theme["card_bg"],
            "hoverColor": css_theme["sidebar_radio_bg"],
            "textColor": css_theme["body_strong"],
            "accentColor": palette["accent"],
        },
        width="stretch",
        height=52,
    )


