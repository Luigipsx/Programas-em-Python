from html import escape
import inspect
from pathlib import Path
from urllib.parse import quote

import streamlit as st

ASSETS = Path(__file__).with_name("assets")
ICONS = {
    "spark": '<path d="m12 3 2.2 6.8L21 12l-6.8 2.2L12 21l-2.2-6.8L3 12l6.8-2.2Z"/>',
    "grid": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
    "edit": '<path d="m15 5 4 4M4 20l4-1L20 7a2.8 2.8 0 0 0-4-4L4 15Z"/>',
    "trash": '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/>',
    "arrow": '<path d="M5 12h14m-6-6 6 6-6 6"/>',
    "leaf": '<path d="M20 4C7 2 2 10 6 17c7 5 15-1 14-13ZM4 21 15 10"/>',
    "heart": '<path d="M20 5a5 5 0 0 0-8 1 5 5 0 0 0-8-1c-5 5 2 11 8 15 6-4 13-10 8-15Z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
}


def icon(name, size=20):
    # Imagens SVG passam pela sanitização de st.html sem conteúdo executável.
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
           'viewBox="0 0 24 24" fill="none" stroke="#41684b" stroke-width="1.7" '
           'stroke-linecap="round" stroke-linejoin="round">'
           + ICONS.get(name, ICONS["grid"]) + "</svg>")
    source = "data:image/svg+xml," + quote(svg, safe="")
    return f'<img class="festa-icon" src="{source}" width="{size}" height="{size}" alt="" aria-hidden="true">'


def apply_theme():
    st.html(ASSETS / "theme.css")
    # O CSS funciona sem JavaScript; versões recentes ganham revelação por rolagem.
    if "unsafe_allow_javascript" in inspect.signature(st.html).parameters:
        st.html("<script>" + (ASSETS / "enhancements.js").read_text(encoding="utf-8") + "</script>",
                unsafe_allow_javascript=True)


def page_header(title, description, category="PLANEJAMENTO DA FESTA"):
    with st.container(key="page-heading"):
        st.html(f'<div class="festa-eyebrow" data-festa-page="{escape(title, quote=True)}"><span></span>{escape(category)}</div>')
        st.title(title)
        st.caption(description)


def section_header(title, description="", badge="", symbol="grid"):
    st.html(
        '<div class="festa-section-heading" data-festa-animate>'
        f'<div class="festa-section-icon">{icon(symbol)}</div><div>'
        f'<h2>{escape(title)}</h2>'
        + (f'<p>{escape(description)}</p>' if description else "")
        + '</div>'
        + (f'<span class="festa-counter">{escape(str(badge))}</span>' if badge else "")
        + '</div>'
    )


def editor_header(record, namespace, noun="registro"):
    action = st.session_state.get(f"{namespace}_action")
    focus = ' data-festa-focus="true"' if action == "edit" else ""
    title = f"Editar {noun}" if record else f"Novo {noun}"
    subtitle = record.get("nome", f"Registro #{record['id']}") if record else "Preencha os dados para começar."
    st.html(f'<div id="editor-{escape(namespace)}" class="festa-editor-heading"{focus}>'
            f'<span class="festa-editor-icon">{icon("edit")}</span><div><h3>{escape(title)}</h3>'
            f'<p>{escape(subtitle)}</p></div><span class="festa-required">* obrigatório</span></div>')


def sidebar_brand():
    st.html('<div class="festa-brand"><span class="festa-brand-mark"><i></i><i></i><i></i><i></i></span>'
            '<div>festa<span>IFC · CAMPUS BLUMENAU</span></div></div>'
            '<div class="festa-sidebar-label">ESPAÇO DE ORGANIZAÇÃO</div>')


def sidebar_footer():
    st.html('<div class="festa-sidebar-note">' + icon("spark", 24)
            + '<strong>Uma festa, muitas mãos.</strong>'
            '<p>Cada contribuição faz parte de algo maior.</p></div>'
            '<div class="festa-sidebar-footer">Planeje. Compartilhe. Celebre.</div>')


def empty_state(title, message):
    st.html('<div class="festa-empty" data-festa-animate>'
            f'<span>{icon("leaf", 28)}</span><strong>{escape(title)}</strong>'
            f'<p>{escape(message)}</p></div>')