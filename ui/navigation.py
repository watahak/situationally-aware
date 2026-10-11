from __future__ import annotations

import html

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

  // Force the component's host containers to auto-size
  let el = parentElement;
  for (let i = 0; i < 6 && el; i++) {
    if (el.style) {
      el.style.height = "auto";
      el.style.overflow = "visible";
    }
    // Stop at the sidebar boundary
    if (el.getAttribute && el.getAttribute("data-testid") === "stSidebar") break;
    el = el.parentElement;
  }

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
      return;
    }

    const headings = Array.from(panel.querySelectorAll("h2")).filter(h => {
      const text = (h.textContent || "").trim();
      if (!text) return false;
      // Skip headings inside closed expanders
      const expander = h.closest("[data-testid='stExpander']");
      if (expander) {
        const details = expander.matches("details") ? expander : expander.querySelector("details");
        if (details && !details.open) return false;
      }
      return true;
    });

    if (!headings.length) {
      nav.innerHTML = '<div class="mq-toc-empty">No sections on this tab.</div>';
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
        height=350,
    )


def build_tab_arrows_html(
    tab_index: int,
    tab_count: int,
    tab_labels: list[str],
    theme_mode: str,
) -> str:
    """Build tab-to-tab arrows to place at the bottom of each tab."""
    mode = theme_mode if theme_mode in {"light", "dark"} else "dark"
    css_theme = _css_theme(mode)
    palette = get_active_palette(mode)

    labels = list(tab_labels)
    if len(labels) < tab_count:
        labels.extend(f"Tab {i + 1}" for i in range(len(labels), tab_count))

    has_prev = tab_index > 0
    has_next = tab_index < (tab_count - 1)

    prev_index = tab_index - 1
    next_index = tab_index + 1

    prev_label = html.escape(labels[prev_index]) if has_prev else ""
    next_label = html.escape(labels[next_index]) if has_next else ""

    prev_visibility = "visible" if has_prev else "hidden"
    next_visibility = "visible" if has_next else "hidden"

    return f"""
<div
  data-role="mini-quant-tab-arrows"
  style="--arrow-border:{css_theme['card_border']};--arrow-bg:{css_theme['card_bg']};--arrow-hover:{css_theme['sidebar_radio_bg']};--arrow-text:{css_theme['body_strong']};--arrow-accent:{palette['accent']};"
>
  <button type="button" data-target-index="{prev_index}" style="visibility:{prev_visibility};">&#8592; Prev: {prev_label}</button>
  <button type="button" data-target-index="{next_index}" style="visibility:{next_visibility};">Next: {next_label} &#8594;</button>
</div>
<script>
(() => {{
  const root = document.currentScript && document.currentScript.previousElementSibling;
  if (!root) return;
  const top = window.parent || window;
  const topDoc = top.document;

  root.querySelectorAll('button[data-target-index]').forEach(button => {{
    button.onclick = () => {{
      const idx = Number(button.getAttribute('data-target-index'));
      if (!Number.isFinite(idx) || idx < 0) return;
      const tabs = topDoc.querySelectorAll('button[role="tab"]');
      if (tabs[idx]) {{
        tabs[idx].click();
        top.scrollTo({{ top: 0, behavior: 'smooth' }});
      }}
    }};
  }});
}})();
</script>
<style>
  [data-role="mini-quant-tab-arrows"] {{
    display: flex;
    gap: 0.5rem;
    justify-content: space-between;
    align-items: center;
    margin-top: 1rem;
    padding-top: 0.35rem;
  }}
  [data-role="mini-quant-tab-arrows"] > button {{
    border: 1px solid var(--arrow-border);
    background: var(--arrow-bg);
    color: var(--arrow-text);
    border-radius: 999px;
    font-size: 0.86rem;
    line-height: 1;
    font-weight: 600;
    padding: 0.55rem 0.82rem;
    cursor: pointer;
    transition: transform 140ms, border-color 140ms, background-color 140ms, color 140ms;
    min-width: 9rem;
    text-align: center;
  }}
  [data-role="mini-quant-tab-arrows"] > button:hover {{
    transform: translateY(-1px);
    border-color: var(--arrow-accent);
    background: var(--arrow-hover);
  }}
  [data-role="mini-quant-tab-arrows"] > button:active {{
    transform: translateY(0);
  }}
  @media (max-width: 720px) {{
    [data-role="mini-quant-tab-arrows"] {{
      flex-direction: column;
      align-items: stretch;
    }}
    [data-role="mini-quant-tab-arrows"] > button {{
      width: 100%;
    }}
  }}
</style>
"""
