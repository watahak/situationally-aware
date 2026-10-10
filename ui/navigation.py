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
    border-radius: 0.7rem;
    padding: 0.7rem 0.75rem;
    background: var(--toc-bg);
  }

  [data-role="toc-title"] {
    color: var(--toc-title);
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
  }

  [data-role="toc-nav"] {
    display: flex;
    flex-direction: column;
    gap: 0.18rem;
    max-height: none;
    overflow-y: visible;
  }

  [data-role="toc-link"] {
    border-left: 2px solid transparent;
    color: var(--toc-text);
    font-size: 0.82rem;
    line-height: 1.35;
    opacity: 0.88;
    text-decoration: none;
    padding: 0.26rem 0.5rem;
    border-radius: 0.35rem;
    transition: border-color 150ms ease, color 150ms ease, background-color 150ms ease, opacity 150ms ease;
  }

  [data-role="toc-link"]:hover {
    opacity: 1;
    color: var(--toc-strong);
    background: var(--toc-hover-bg);
  }

  [data-role="toc-link"][data-active="true"] {
    opacity: 1;
    color: var(--toc-strong);
    border-left-color: var(--toc-accent);
    background: var(--toc-active-bg);
  }

  [data-role="toc-note"] {
    color: var(--toc-muted);
    font-size: 0.78rem;
    padding: 0.2rem 0;
  }
</style>
""",
    js="""
const instances =
  window.__miniQuantSidebarTocInstances ||
  (window.__miniQuantSidebarTocInstances = new WeakMap());

function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\\s-]/g, "")
    .trim()
    .replace(/\\s+/g, "-")
    .replace(/-+/g, "-");
}

function getRootContext() {
  let rootWin = window;
  let rootDoc = document;

  try {
    if (window.parent && window.parent !== window && window.parent.document) {
      rootWin = window.parent;
      rootDoc = window.parent.document;
    }
  } catch (_err) {
    // Fallback to local document when parent is not accessible.
  }

  return { rootWin, rootDoc };
}

function queryAllDeep(root, selector) {
  const out = [];

  const walk = (node) => {
    if (!node) return;

    if (node.nodeType === Node.ELEMENT_NODE && node.matches && node.matches(selector)) {
      out.push(node);
    }

    const shadowRoot = node.shadowRoot || null;
    if (shadowRoot) {
      walk(shadowRoot);
    }

    const children = node.children || [];
    for (const child of children) {
      walk(child);
    }
  };

  walk(root);
  return out;
}

function queryOneDeep(root, selector) {
  const matches = queryAllDeep(root, selector);
  return matches.length ? matches[0] : null;
}

function findByIdDeep(root, id) {
  if (!id) return null;
  const stack = [root];

  while (stack.length) {
    const node = stack.pop();
    if (!node) continue;

    if (node.nodeType === Node.ELEMENT_NODE && node.id === id) {
      return node;
    }

    if (node.shadowRoot) {
      stack.push(node.shadowRoot);
    }

    const children = node.children || [];
    for (let i = children.length - 1; i >= 0; i -= 1) {
      stack.push(children[i]);
    }
  }

  return null;
}

function findActivePanel(rootDoc) {
  const tabs = queryAllDeep(rootDoc, '[role="tab"]');
  const activeTab = tabs.find((tab) => tab.getAttribute("aria-selected") === "true");
  const panels = queryAllDeep(rootDoc, '[role="tabpanel"]');

  if (!activeTab) {
    if (panels.length === 1) return panels[0];
    return panels.find((panel) => panel.getAttribute("aria-hidden") !== "true") || null;
  }

  const controlledPanelId = activeTab.getAttribute("aria-controls");
  if (controlledPanelId) {
    const controlledPanel = findByIdDeep(rootDoc, controlledPanelId);
    if (controlledPanel && controlledPanel.getAttribute("role") === "tabpanel") {
      return controlledPanel;
    }
  }

  if (panels.length === 1) {
    return panels[0];
  }

  const activeIndex = tabs.indexOf(activeTab);
  if (activeIndex < 0) return null;
  return panels[activeIndex] || panels.find((panel) => panel.getAttribute("aria-hidden") !== "true") || null;
}

function isElementVisible(element, rootWin) {
  if (!element) return false;
  if (element.closest('[aria-hidden="true"]')) return false;

  const style = rootWin.getComputedStyle(element);
  if (style.display === "none" || style.visibility === "hidden") return false;

  const rect = element.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
}

function isInsideClosedExpander(element) {
  const expander = element.closest('[data-testid="stExpander"]');
  if (!expander) return false;

  const details = expander.matches('details') ? expander : expander.querySelector('details');
  if (!details) return false;
  return details.open === false;
}

function setThemeVars(shell, data) {
  const palette = {
    tocBg: "transparent",
    tocTitle: "#94A3B8",
    tocText: "#B5C4D9",
    tocStrong: "#E2E8F0",
    tocMuted: "#94A3B8",
    tocAccent: "#38BDF8",
    tocDivider: "rgba(255,255,255,0.08)",
    tocHoverBg: "rgba(56, 189, 248, 0.08)",
    tocActiveBg: "rgba(56, 189, 248, 0.12)",
    ...(data || {}),
  };

  shell.style.setProperty("--toc-bg", palette.tocBg);
  shell.style.setProperty("--toc-title", palette.tocTitle);
  shell.style.setProperty("--toc-text", palette.tocText);
  shell.style.setProperty("--toc-strong", palette.tocStrong);
  shell.style.setProperty("--toc-muted", palette.tocMuted);
  shell.style.setProperty("--toc-accent", palette.tocAccent);
  shell.style.setProperty("--toc-divider", palette.tocDivider);
  shell.style.setProperty("--toc-hover-bg", palette.tocHoverBg);
  shell.style.setProperty("--toc-active-bg", palette.tocActiveBg);
}

export default function(component) {
  const { parentElement, data } = component;
  if (!parentElement) return;
  const { rootWin, rootDoc } = getRootContext();

  const shell = parentElement.querySelector('[data-role="toc-shell"]');
  const nav = parentElement.querySelector('[data-role="toc-nav"]');
  if (!shell || !nav) return;

  setThemeVars(shell, data);

  let state = instances.get(parentElement);
  if (!state) {
    state = {
      cleanup: null,
      activeId: null,
      linksById: new Map(),
      headings: [],
      visibleHeadingTops: new Map(),
    };
    instances.set(parentElement, state);
  }

  if (state.cleanup) state.cleanup();

  const teardowns = [];
  state.activeId = null;
  state.linksById.clear();
  state.headings = [];
  state.visibleHeadingTops.clear();

  function setActive(id) {
    if (!id || state.activeId === id) return;
    state.activeId = id;
    state.linksById.forEach((link, linkId) => {
      if (linkId === id) {
        link.setAttribute("data-active", "true");
      } else {
        link.removeAttribute("data-active");
      }
    });
  }

  function pickActiveByViewport() {
    if (!state.headings.length) return;
    const threshold = rootWin.innerHeight * 0.2;
    let candidate = null;

    for (const heading of state.headings) {
      const top = heading.getBoundingClientRect().top;
      if (top <= threshold) {
        candidate = heading;
      }
    }

    if (!candidate) {
      candidate = state.headings.find((heading) => heading.getBoundingClientRect().top > 0);
    }

    if (!candidate) {
      candidate = state.headings[state.headings.length - 1];
    }

    if (candidate && candidate.id) {
      setActive(candidate.id);
    }
  }

  function ensureHeadingId(heading, usedIds) {
    const existing = (heading.id || "").trim();
    if (existing) {
      usedIds.add(existing);
      return existing;
    }

    const text = (heading.textContent || "").trim();
    const base = `toc-${slugify(text) || "section"}`;
    let unique = base;
    let count = 2;
    while (usedIds.has(unique) || (rootDoc.getElementById(unique) && rootDoc.getElementById(unique) !== heading)) {
      unique = `${base}-${count}`;
      count += 1;
    }

    heading.id = unique;
    usedIds.add(unique);
    return unique;
  }

  function rebuildToc() {
    nav.innerHTML = "";
    state.linksById.clear();
    state.headings = [];
    state.visibleHeadingTops.clear();
    state.activeId = null;

    const panel = findActivePanel(rootDoc);

    let headings = [];

    if (panel) {
      headings = queryAllDeep(panel, "h2").filter((heading) => {
        return (
          Boolean((heading.textContent || "").trim())
          && isElementVisible(heading, rootWin)
          && !isInsideClosedExpander(heading)
          && !shell.contains(heading)
        );
      });
    }

    // Sidebar renders before tab content, so fallback to visible main headings
    // while the active panel is not yet fully mounted.
    if (!headings.length) {
      const mainRoot = queryOneDeep(rootDoc, '[data-testid="stMain"]');
      if (mainRoot) {
        headings = queryAllDeep(mainRoot, "h2").filter((heading) => {
          return (
            Boolean((heading.textContent || "").trim())
            && isElementVisible(heading, rootWin)
            && !isInsideClosedExpander(heading)
            && !shell.contains(heading)
          );
        });
      }
    }

    if (!headings.length) {
      const note = nav.ownerDocument.createElement("div");
      note.setAttribute("data-role", "toc-note");
      note.textContent = "No headings available on this tab.";
      nav.appendChild(note);
      return;
    }

    const usedIds = new Set();
    headings.forEach((heading) => {
      const id = ensureHeadingId(heading, usedIds);
      const text = (heading.textContent || "").trim();
      const link = nav.ownerDocument.createElement("a");
      link.href = `#${id}`;
      link.textContent = text;
      link.setAttribute("data-role", "toc-link");
      link.setAttribute("data-target-id", id);

      const onClick = (event) => {
        event.preventDefault();
        heading.scrollIntoView({ behavior: "smooth", block: "start" });
      };

      link.addEventListener("click", onClick);
      teardowns.push(() => link.removeEventListener("click", onClick));

      nav.appendChild(link);
      state.linksById.set(id, link);
    });

    state.headings = headings;

    if (rootWin.IntersectionObserver) {
      const observer = new rootWin.IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            const id = entry.target.id;
            if (!id) return;
            if (entry.isIntersecting) {
              state.visibleHeadingTops.set(id, entry.boundingClientRect.top);
            } else {
              state.visibleHeadingTops.delete(id);
            }
          });

          if (state.visibleHeadingTops.size > 0) {
            let winnerId = null;
            let smallestDistance = Number.POSITIVE_INFINITY;
            state.visibleHeadingTops.forEach((top, id) => {
              const distance = Math.abs(top);
              if (distance < smallestDistance) {
                smallestDistance = distance;
                winnerId = id;
              }
            });
            if (winnerId) setActive(winnerId);
          } else {
            pickActiveByViewport();
          }
        },
        { root: null, rootMargin: "-10% 0px -80% 0px", threshold: [0, 1] }
      );

      headings.forEach((heading) => observer.observe(heading));
      teardowns.push(() => observer.disconnect());
    }

    let pendingFrame = null;
    const onScroll = () => {
      if (pendingFrame !== null) return;
      pendingFrame = rootWin.requestAnimationFrame(() => {
        pendingFrame = null;
        if (state.visibleHeadingTops.size === 0) {
          pickActiveByViewport();
        }
      });
    };

    rootWin.addEventListener("scroll", onScroll, { passive: true });
    teardowns.push(() => {
      rootWin.removeEventListener("scroll", onScroll);
      if (pendingFrame !== null) {
        rootWin.cancelAnimationFrame(pendingFrame);
      }
    });

    pickActiveByViewport();
  }

  let scheduledRebuild = null;
  const scheduleRebuild = () => {
    if (scheduledRebuild !== null) return;
    scheduledRebuild = rootWin.setTimeout(() => {
      scheduledRebuild = null;
      rebuildToc();
    }, 20);
  };

  rebuildToc();
  scheduleRebuild();

  const tablist = queryOneDeep(rootDoc, '[role="tablist"]');
  if (tablist) {
    const tabObserver = new rootWin.MutationObserver((mutations) => {
      if (mutations.some((mutation) => mutation.attributeName === "aria-selected")) {
        scheduleRebuild();
      }
    });

    tabObserver.observe(tablist, {
      attributes: true,
      subtree: true,
      attributeFilter: ["aria-selected"],
    });

    teardowns.push(() => tabObserver.disconnect());

    const tabButtons = queryAllDeep(tablist, '[role="tab"]');
    tabButtons.forEach((tabButton) => {
      const onClick = () => {
        scheduleRebuild();
      };
      tabButton.addEventListener("click", onClick);
      teardowns.push(() => tabButton.removeEventListener("click", onClick));
    });
  }

  const mainRoot = queryOneDeep(rootDoc, '[data-testid="stMain"]');
  if (mainRoot) {
    const contentObserver = new rootWin.MutationObserver(() => {
      scheduleRebuild();
    });
    contentObserver.observe(mainRoot, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["style", "class", "hidden", "aria-hidden"],
    });
    teardowns.push(() => contentObserver.disconnect());
  }

  let lastActiveTabKey = null;
  const syncActiveTab = () => {
    const tabs = queryAllDeep(rootDoc, '[role="tab"]');
    const activeTab = tabs.find((tab) => tab.getAttribute("aria-selected") === "true") || null;
    const nextKey = activeTab
      ? `${activeTab.getAttribute("id") || ""}|${(activeTab.textContent || "").trim()}`
      : "";

    if (nextKey !== lastActiveTabKey) {
      lastActiveTabKey = nextKey;
      scheduleRebuild();
    }
  };

  syncActiveTab();
  const tabSyncTimer = rootWin.setInterval(syncActiveTab, 220);
  teardowns.push(() => rootWin.clearInterval(tabSyncTimer));

  state.cleanup = () => {
    while (teardowns.length) {
      const teardown = teardowns.pop();
      try {
        teardown();
      } catch (_err) {
        // Keep teardown best-effort to avoid rerun crashes.
      }
    }
    state.linksById.clear();
    state.headings = [];
    state.visibleHeadingTops.clear();
    if (scheduledRebuild !== null) {
      rootWin.clearTimeout(scheduledRebuild);
      scheduledRebuild = null;
    }
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

    # Streamlit's component host can keep a stale fixed height; force auto sizing.
    st.html(
        """
<style>
  [data-testid="stElementContainer"].st-key-mini-quant-sidebar-toc,
  [data-testid="stElementContainer"].st-key-mini-quant-sidebar-toc .stBidiComponent,
  [data-testid="stElementContainer"].st-key-mini-quant-sidebar-toc [data-testid="stBidiComponentIsolated"] {
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
  }

  [data-testid="stElementContainer"].st-key-mini-quant-sidebar-toc [data-testid="stBidiComponentIsolated"] {
    overflow: visible !important;
  }
</style>
"""
    )

    _TOC_COMPONENT(
        key="mini-quant-sidebar-toc",
        data={
            "tocBg": "transparent",
            "tocTitle": css_theme["sidebar_muted"],
            "tocText": css_theme["sidebar_caption"],
            "tocStrong": css_theme["body_strong"],
            "tocMuted": css_theme["sidebar_muted"],
            "tocAccent": palette["accent"],
            "tocDivider": css_theme["sidebar_divider"],
            "tocHoverBg": css_theme["sidebar_radio_bg"],
            "tocActiveBg": palette["accent_fill"],
        },
        width="stretch",
        height="content",
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
  data-current-index="{tab_index}"
  style="--arrow-border:{css_theme['card_border']};--arrow-bg:{css_theme['card_bg']};--arrow-hover:{css_theme['sidebar_radio_bg']};--arrow-text:{css_theme['body_strong']};--arrow-accent:{palette['accent']};"
>
  <button type="button" data-target-index="{prev_index}" style="visibility:{prev_visibility};">&#8592; Prev: {prev_label}</button>
  <button type="button" data-target-index="{next_index}" style="visibility:{next_visibility};">Next: {next_label} &#8594;</button>
</div>
<script>
(() => {{
  const root = document.currentScript && document.currentScript.previousElementSibling;
  if (!root) return;

  let rootWin = window;
  let rootDoc = document;
  try {{
    if (window.parent && window.parent !== window && window.parent.document) {{
      rootWin = window.parent;
      rootDoc = window.parent.document;
    }}
  }} catch (_err) {{
    rootWin = window;
    rootDoc = document;
  }}

  const queryAllDeep = (start, selector) => {{
    const out = [];
    const walk = (node) => {{
      if (!node) return;
      if (node.nodeType === Node.ELEMENT_NODE && node.matches && node.matches(selector)) {{
        out.push(node);
      }}
      if (node.shadowRoot) walk(node.shadowRoot);
      const children = node.children || [];
      for (const child of children) walk(child);
    }};
    walk(start);
    return out;
  }};

  const scrollToTop = () => {{
    const main = queryAllDeep(rootDoc, '[data-testid="stMain"]')[0] || null;
    if (main && typeof main.scrollTo === "function") {{
      main.scrollTo({{ top: 0, behavior: "smooth" }});
      return;
    }}
    rootWin.scrollTo({{ top: 0, behavior: "smooth" }});
  }};

  root.querySelectorAll('button[data-target-index]').forEach((button) => {{
    button.onclick = () => {{
      const targetIndex = Number(button.getAttribute("data-target-index"));
      if (!Number.isFinite(targetIndex)) return;
      if (targetIndex < 0) return;

      const tabs = queryAllDeep(rootDoc, '[role="tab"]');
      const targetTab = tabs[targetIndex];
      if (!targetTab) return;

      targetTab.click();
      scrollToTop();
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
    transition: transform 140ms ease, border-color 140ms ease, background-color 140ms ease, color 140ms ease;
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