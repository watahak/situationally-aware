import streamlit as st


PALETTE_DARK = {
    "base": "#0E1117",
    "card": "#161B22",
    "slate": "#1E293B",
    "accent": "#38BDF8",
    "accent_fill": "rgba(56, 189, 248, 0.08)",
    "green": "#10B981",
    "red": "#EF4444",
    "amber": "#FBBF24",
    "text": "#E2E8F0",
    "muted": "#94A3B8",
    "grid": "rgba(255, 255, 255, 0.05)",
}

PALETTE_LIGHT = {
    "base": "#F8FAFC",
    "card": "#FFFFFF",
    "slate": "#E2E8F0",
    "accent": "#0284C7",
    "accent_fill": "rgba(2, 132, 199, 0.12)",
    "green": "#059669",
    "red": "#DC2626",
    "amber": "#D97706",
    "text": "#0F172A",
    "muted": "#1E293B",
    "grid": "rgba(15, 23, 42, 0.12)",
}


_THEME_SYNC = st.components.v2.component(
        "mini_quant_theme_sync",
        html="""
<div data-role="theme-sync" style="display:none;width:0;height:0;overflow:hidden;"></div>
""",
        js="""
const instances =
    window.__miniQuantThemeSyncInstances ||
    (window.__miniQuantThemeSyncInstances = new WeakMap());

function parseColor(color) {
    if (!color) return null;
    const value = color.trim().toLowerCase();

    const rgbMatch = value.match(/rgba?\\(([^)]+)\\)/);
    if (rgbMatch) {
        const parts = rgbMatch[1]
            .split(',')
            .slice(0, 3)
            .map((part) => Number.parseFloat(part.trim()));
        if (parts.every((p) => Number.isFinite(p))) {
            return parts.map((p) => Math.max(0, Math.min(255, p)));
        }
    }

    const hex = value.replace('#', '');
    if (hex.length === 3) {
        const full = hex.split('').map((c) => c + c).join('');
        return [
            Number.parseInt(full.slice(0, 2), 16),
            Number.parseInt(full.slice(2, 4), 16),
            Number.parseInt(full.slice(4, 6), 16),
        ];
    }
    if (hex.length === 6) {
        return [
            Number.parseInt(hex.slice(0, 2), 16),
            Number.parseInt(hex.slice(2, 4), 16),
            Number.parseInt(hex.slice(4, 6), 16),
        ];
    }

    return null;
}

function detectMode(parentElement) {
    const host = parentElement.host || parentElement;
    const hostStyle = getComputedStyle(host);
    const rootStyle = getComputedStyle(document.documentElement);

    const bgColor =
        hostStyle.getPropertyValue('--st-background-color').trim() ||
        rootStyle.getPropertyValue('--st-background-color').trim();

    const rgb = parseColor(bgColor);
    if (rgb) {
        const [r, g, b] = rgb;
        const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
        return luminance < 0.52 ? 'dark' : 'light';
    }

    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }

    return 'light';
}

export default function (component) {
    const { parentElement, data, setStateValue } = component;
    if (!parentElement) return;

    let state = instances.get(parentElement);
    if (!state) {
        state = {
            knownMode: null,
            emit: null,
            observer: null,
            mediaQuery: null,
            mediaHandler: null,
        };
        instances.set(parentElement, state);
    }

    state.knownMode = data?.mode ?? null;

    const emitIfChanged = () => {
        const detected = detectMode(parentElement);
        if (detected && detected !== state.knownMode) {
            setStateValue('mode', detected);
        }
    };

    state.emit = emitIfChanged;

    if (!state.observer) {
        state.observer = new MutationObserver(() => {
            if (state.emit) state.emit();
        });
        state.observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class', 'style', 'data-theme'],
        });
    }

    if (!state.mediaQuery && window.matchMedia) {
        state.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        state.mediaHandler = () => {
            if (state.emit) state.emit();
        };
        if (state.mediaQuery.addEventListener) {
            state.mediaQuery.addEventListener('change', state.mediaHandler);
        } else if (state.mediaQuery.addListener) {
            state.mediaQuery.addListener(state.mediaHandler);
        }
    }

    requestAnimationFrame(emitIfChanged);

    return () => {
        if (state.observer) {
            state.observer.disconnect();
            state.observer = null;
        }
        if (state.mediaQuery && state.mediaHandler) {
            if (state.mediaQuery.removeEventListener) {
                state.mediaQuery.removeEventListener('change', state.mediaHandler);
            } else if (state.mediaQuery.removeListener) {
                state.mediaQuery.removeListener(state.mediaHandler);
            }
        }
        state.mediaQuery = null;
        state.mediaHandler = null;
        state.emit = null;
        instances.delete(parentElement);
    };
}
""",
)


def resolve_theme_mode() -> str:
    """Read Streamlit theme type with a safe dark fallback."""
    try:
        theme_type = getattr(st.context.theme, "type", None)
    except Exception:
        theme_type = None
    return theme_type if theme_type in {"light", "dark"} else "dark"


def get_plotly_template(theme_mode: str) -> str:
    return "plotly_light" if theme_mode == "light" else "plotly_dark"


def get_live_theme_mode(*, key: str = "mini-quant-theme-sync") -> str:
    """Return a theme mode that updates when users toggle app light/dark mode.

    Streamlit's Python script only sees front-end changes on rerun. This watcher
    emits a component state change only when the detected mode differs from the
    last known mode, triggering a single rerun per actual theme switch.
    """
    known_mode = st.session_state.get("_mini_quant_theme_mode")
    if known_mode not in {"light", "dark"}:
        known_mode = resolve_theme_mode()

    state = _THEME_SYNC(
        key=key,
        data={"mode": known_mode},
        width="content",
        height=0,
        on_mode_change=lambda: None,
    )
    synced_mode = getattr(state, "mode", None)

    if synced_mode in {"light", "dark"}:
        st.session_state["_mini_quant_theme_mode"] = synced_mode
        return synced_mode

    return known_mode


def get_active_palette(theme_mode: str) -> dict[str, str]:
    return PALETTE_LIGHT if theme_mode == "light" else PALETTE_DARK


def _css_theme(theme_mode: str) -> dict[str, str]:
    if theme_mode == "light":
        return {
            "app_bg": (
                "radial-gradient(ellipse 80% 60% at 15% 20%, rgba(2, 132, 199, 0.14) 0%, transparent 68%),"
                "radial-gradient(ellipse 60% 80% at 85% 30%, rgba(5, 150, 105, 0.09) 0%, transparent 58%),"
                "radial-gradient(ellipse 70% 50% at 50% 82%, rgba(59, 130, 246, 0.08) 0%, transparent 62%),"
                "radial-gradient(ellipse 40% 40% at 70% 60%, rgba(217, 119, 6, 0.05) 0%, transparent 48%),"
                "linear-gradient(170deg, #F8FBFF 0%, #F3F7FC 38%, #ECF3FA 100%)"
            ),
            "card_bg": "rgba(255, 255, 255, 0.84)",
            "card_border": "rgba(15, 23, 42, 0.12)",
            "card_shadow": "0 4px 24px rgba(15, 23, 42, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.7)",
            "card_hover_border": "rgba(2, 132, 199, 0.35)",
            "card_hover_shadow": "0 10px 28px rgba(15, 23, 42, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.85)",
            "h1": "#0F172A",
            "h2": "#0F172A",
            "h3": "#0F172A",
            "h2_border": "rgba(15, 23, 42, 0.12)",
            "body_text": "#0F172A",
            "body_strong": "#0F172A",
            "caption": "#1E293B",
            "sidebar_bg": "rgba(248, 250, 252, 0.9)",
            "sidebar_border": "rgba(15, 23, 42, 0.12)",
            "sidebar_muted": "#334155",
            "sidebar_caption": "#0F172A",
            "sidebar_radio_bg": "rgba(226, 232, 240, 0.68)",
            "sidebar_radio_border": "rgba(15, 23, 42, 0.1)",
            "sidebar_radio_hover_bg": "rgba(226, 232, 240, 0.95)",
            "sidebar_radio_hover_border": "rgba(2, 132, 199, 0.28)",
            "sidebar_radio_checked_bg": "rgba(2, 132, 199, 0.12)",
            "sidebar_radio_checked_border": "rgba(2, 132, 199, 0.4)",
            "sidebar_checkbox_bg": "rgba(226, 232, 240, 0.52)",
            "sidebar_checkbox_border": "rgba(15, 23, 42, 0.08)",
            "sidebar_checkbox_hover_border": "rgba(2, 132, 199, 0.24)",
            "sidebar_divider": "rgba(15, 23, 42, 0.14)",
            "expander": "#0F172A",
        }

    return {
        "app_bg": (
            "radial-gradient(ellipse 80% 60% at 15% 20%, rgba(56, 189, 248, 0.07) 0%, transparent 70%),"
            "radial-gradient(ellipse 60% 80% at 85% 30%, rgba(16, 185, 129, 0.05) 0%, transparent 60%),"
            "radial-gradient(ellipse 70% 50% at 50% 80%, rgba(139, 92, 246, 0.04) 0%, transparent 65%),"
            "radial-gradient(ellipse 40% 40% at 70% 60%, rgba(251, 191, 36, 0.025) 0%, transparent 50%),"
            "linear-gradient(170deg, #0E1117 0%, #0C0F16 40%, #10131A 100%)"
        ),
        "card_bg": "rgba(22, 27, 34, 0.55)",
        "card_border": "rgba(255, 255, 255, 0.1)",
        "card_shadow": "0 4px 24px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.04)",
        "card_hover_border": "rgba(56, 189, 248, 0.4)",
        "card_hover_shadow": "0 8px 32px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.06)",
        "h1": "#F1F5F9",
        "h2": "#E2E8F0",
        "h3": "#CBD5E1",
        "h2_border": "rgba(255, 255, 255, 0.06)",
        "body_text": "#A8B7C9",
        "body_strong": "#E2E8F0",
        "caption": "#CBD5E1",
        "sidebar_bg": "rgba(14, 17, 23, 0.85)",
        "sidebar_border": "rgba(255, 255, 255, 0.06)",
        "sidebar_muted": "#94A3B8",
        "sidebar_caption": "#B5C4D9",
        "sidebar_radio_bg": "rgba(30, 41, 59, 0.5)",
        "sidebar_radio_border": "rgba(255, 255, 255, 0.06)",
        "sidebar_radio_hover_bg": "rgba(30, 41, 59, 0.8)",
        "sidebar_radio_hover_border": "rgba(56, 189, 248, 0.3)",
        "sidebar_radio_checked_bg": "rgba(56, 189, 248, 0.08)",
        "sidebar_radio_checked_border": "rgba(56, 189, 248, 0.5)",
        "sidebar_checkbox_bg": "rgba(30, 41, 59, 0.3)",
        "sidebar_checkbox_border": "rgba(255, 255, 255, 0.04)",
        "sidebar_checkbox_hover_border": "rgba(56, 189, 248, 0.2)",
        "sidebar_divider": "rgba(255, 255, 255, 0.06)",
        "expander": "#CBD5E1",
    }


def build_theme_css(theme_mode: str) -> str:
    css_theme = _css_theme(theme_mode)

    return f"""
<style>
.stApp {{
    background: {css_theme["app_bg"]} !important;
    overflow-x: hidden !important;
}}

html,
body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {{
    max-width: 100%;
    overflow-x: hidden !important;
}}

[data-testid="stMainBlockContainer"] > div,
div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"] {{
    min-width: 0 !important;
}}

div[data-testid="stVerticalBlock"] > div[data-testid="stBlock"] {{
    background: {css_theme["card_bg"]} !important;
    border: 1px solid {css_theme["card_border"]} !important;
    box-shadow: {css_theme["card_shadow"]} !important;
    overflow-x: clip;
}}

div[data-testid="stVerticalBlock"] > div[data-testid="stBlock"]:hover {{
    border-color: {css_theme["card_hover_border"]} !important;
    box-shadow: {css_theme["card_hover_shadow"]} !important;
}}

h1[data-testid="stHeading"] {{
    color: {css_theme["h1"]} !important;
    font-size: clamp(1.75rem, 1.5rem + 1.2vw, 2.4rem) !important;
}}

h2[data-testid="stHeading"] {{
    color: {css_theme["h2"]} !important;
    border-bottom: 1px solid {css_theme["h2_border"]} !important;
    font-size: clamp(1.3rem, 1.15rem + 0.8vw, 1.9rem) !important;
}}

h3[data-testid="stHeading"] {{
    color: {css_theme["h3"]} !important;
    font-size: clamp(1.1rem, 1rem + 0.5vw, 1.4rem) !important;
}}

div[data-testid="stMarkdown"] p {{
    color: {css_theme["body_text"]} !important;
}}

div[data-testid="stMarkdown"] strong {{
    color: {css_theme["body_strong"]} !important;
}}

div[data-testid="stMarkdownContainer"] {{
    max-width: 100% !important;
    overflow-x: auto !important;
}}

div[data-testid="stMarkdownContainer"] table {{
    display: block;
    width: max-content;
    min-width: 100%;
}}

div[data-testid="stMarkdownContainer"] pre {{
    max-width: 100% !important;
    overflow-x: auto !important;
}}

div[data-testid="stMarkdownContainer"] h1,
div[data-testid="stMarkdownContainer"] h2,
div[data-testid="stMarkdownContainer"] h3 {{
    color: {css_theme["h2"]} !important;
    line-height: 1.25 !important;
}}

div[data-testid="stCaptionContainer"] p {{
    color: {css_theme["caption"]} !important;
}}

section[data-testid="stSidebar"] {{
    background: {css_theme["sidebar_bg"]} !important;
    border-right: 1px solid {css_theme["sidebar_border"]} !important;
}}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h4,
section[data-testid="stSidebar"] div[data-testid="stMarkdown"] h4 {{
    color: {css_theme["sidebar_muted"]} !important;
}}

section[data-testid="stSidebar"] h1[data-testid="stHeading"] {{
    margin-top: 0.35rem !important;
    margin-bottom: 0.55rem !important;
    padding-top: 0 !important;
}}

section[data-testid="stSidebar"] div[data-testid="stCaptionContainer"] p {{
    color: {css_theme["sidebar_caption"]} !important;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] label {{
    background: {css_theme["sidebar_radio_bg"]} !important;
    border: 1px solid {css_theme["sidebar_radio_border"]} !important;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
    border-color: {css_theme["sidebar_radio_hover_border"]} !important;
    background: {css_theme["sidebar_radio_hover_bg"]} !important;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"],
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
    border-color: {css_theme["sidebar_radio_checked_border"]} !important;
    background: {css_theme["sidebar_radio_checked_bg"]} !important;
}}

section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label {{
    background: {css_theme["sidebar_checkbox_bg"]} !important;
    border: 1px solid {css_theme["sidebar_checkbox_border"]} !important;
}}

section[data-testid="stSidebar"] div[data-testid="stCheckbox"] label:hover {{
    border-color: {css_theme["sidebar_checkbox_hover_border"]} !important;
}}

section[data-testid="stSidebar"] hr {{
    border-color: {css_theme["sidebar_divider"]} !important;
}}

div[data-testid="stExpander"] summary span p {{
    color: {css_theme["expander"]} !important;
}}

@media (max-width: 900px) {{
    [data-testid="stMainBlockContainer"] {{
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }}
}}

@media (max-width: 768px) {{
    h1[data-testid="stHeading"] {{
        font-size: 1.6rem !important;
        letter-spacing: -0.01em !important;
    }}

    h2[data-testid="stHeading"] {{
        font-size: 1.2rem !important;
        margin-top: 1rem !important;
    }}

    h3[data-testid="stHeading"] {{
        font-size: 1.02rem !important;
    }}

    div[data-testid="stMarkdownContainer"] h1 {{
        font-size: 1.45rem !important;
    }}

    div[data-testid="stMarkdownContainer"] h2 {{
        font-size: 1.2rem !important;
    }}

    div[data-testid="stMarkdownContainer"] h3 {{
        font-size: 1.05rem !important;
    }}

    div[data-testid="stMarkdownContainer"] h4 {{
        font-size: 0.98rem !important;
    }}

    div[data-testid="stVerticalBlock"] > div[data-testid="stBlock"] {{
        padding: 0.82rem;
        border-radius: 10px;
    }}
}}
</style>
"""


def inject_theme_styles(theme_mode: str) -> None:
    st.html(build_theme_css(theme_mode))
