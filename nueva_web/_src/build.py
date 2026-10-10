"""
build.py

Assemble the static pages of the Kyobac Labs website. Every page shares
the same <head>, header (with the Empresas / Pacientes audience tabs),
supporters marquee and footer; only the <main> content changes and it
lives in _src/paginas/<page>.html. Inside those fragments, {{icon:name}}
inserts an inline SVG icon from ICONS. Run it from anywhere:

    python3 _src/build.py

It also writes the knowledge base of "Clara", the website assistant,
to _src/clara/conocimiento.txt: the visible text of the public pages,
which the Cloudflare Worker in _src/clara sends to the language model.
After changing the pages, redeploy the Worker so that Clara learns them:

    cd _src/clara && npx wrangler deploy

Jekyll (GitHub Pages) ignores folders that start with "_", so _src is
not published.

Version: 1.1
Author: Adrian Berenguer-Agustí (I2SysBio-CSIC)
Date: 2026-10-10
"""

import re
import sys
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
from pathlib import Path

# Root folder of the website (parent of _src).
SITE_DIR = Path(__file__).resolve().parent.parent
# Folder with the <main> fragments of each page.
PAGES_DIR = Path(__file__).resolve().parent / "paginas"
# Version and date written in every generated page header.
VERSION = "0.5"
BUILD_DATE = "2026-10-10"
# Contact e-mail and LinkedIn page of the company.
EMAIL = "kyobac.labs@gmail.com"
LINKEDIN = "https://www.linkedin.com/in/kyobac-labs-131b0a3a3/"
# Google Form used to validate the end customer of MycoRelax.
SURVEY_URL = ("https://docs.google.com/forms/d/e/1FAIpQLSet7NSrcqk8EsQy1o"
              "ftCg3dcnevxsJ_NIiP5No1gonkrwAQoQ/viewform")
# Address of Clara's Cloudflare Worker; empty to leave the assistant out.
CLARA_ENDPOINT = "https://clara.kyobaclabs.workers.dev/chat"
# Folder of Clara's Worker and file of the generated knowledge base.
CLARA_DIR = Path(__file__).resolve().parent / "clara"
KNOWLEDGE_FILE = CLARA_DIR / "conocimiento.txt"
# Pages whose text Clara knows; the legal pages are summarised by hand in
# knowledge_appendix() to keep the prompt (and its cost) small.
KNOWLEDGE_PAGES = ["index.html", "soluciones.html", "pipeline.html",
                   "mision.html", "equipo.html", "noticias.html",
                   "empleo.html", "pacientes.html"]
# Pattern of the icon placeholders inside page fragments.
ICON_PATTERN = re.compile(r"\{\{icon:([a-z0-9-]+)\}\}")

# Inner SVG markup of every line icon (24 x 24 viewBox).
ICONS = {
    "arrow": '<path d="M5 12h14M12 5l7 7-7 7"/>',
    "arrow-circle": '<circle cx="12" cy="12" r="10"/>'
                    '<path d="m10.5 8 4 4-4 4"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "down-circle": '<circle cx="12" cy="12" r="10"/>'
                   '<path d="m8 10.5 4 4 4-4"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/>'
            '<path d="m22 7-10 6L2 7"/>',
    "patent": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 '
              '0 2-2V8z"/><path d="M14 2v6h6"/><circle cx="12" cy="14" '
              'r="3"/>',
    "dna": '<path d="M8 3c0 4.5 8 4.5 8 9s-8 4.5-8 9M16 3c0 4.5-8 4.5-8 9s8'
           ' 4.5 8 9M9 6.5h6M9 17.5h6"/>',
    "flask": '<path d="M9 3h6M10 3v6L4.6 18.5A1.7 1.7 0 0 0 6 21h12a1.7 1.7'
             ' 0 0 0 1.4-2.5L14 9V3"/><path d="M7.5 15h9"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15'
             ' 0 0 1 0 20 15 15 0 0 1 0-20"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>'
              '<path d="m9 12 2 2 4-4"/>',
    "chip": '<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" '
            'y="9" width="6" height="6"/><path d="M9 2v3M15 2v3M9 19v3M15'
            ' 19v3M19 9h3M19 15h3M2 9h3M2 15h3"/>',
    "network": '<circle cx="5" cy="6" r="2.5"/><circle cx="19" cy="6" '
               'r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M7.5 '
               '6h9M6.3 8.2l4.4 7.6M17.7 8.2l-4.4 7.6"/>',
    "monitor": '<rect x="2" y="3" width="20" height="14" rx="2"/><path '
               'd="M8 21h8M12 17v4"/><path d="m6 12 3-3 3 3 3-5 3 3"/>',
    "factory": '<path d="M2 20h20M4 20V10l5 3v-3l5 3V6l6 4v10"/>',
    "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8'
            ' 11V7a4 4 0 0 1 8 0v4"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 7v5l3 2"/>',
    "bookmark": '<path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 '
                '2z"/>',
    "key": '<circle cx="7.5" cy="15.5" r="4.5"/><path d="M10.7 12.3 21 2M16'
           ' 7l3 3M18.5 4.5l2 2"/>',
    "leaf": '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.5 19 2c1 2 2 4.2'
            ' 2 8 0 5.5-4.8 10-10 10Z"/><path d="M2 21c0-3 1.9-5.4 5.1-6"/>',
    "university": '<path d="M2 10 12 4l10 6M3 21h18M5 21V10M19 21V10M9 21V'
                  '10M15 21V10"/>',
    "clipboard": '<rect x="8" y="2" width="8" height="4" rx="1"/><path d="M'
                 '16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a'
                 '2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
    "heart": '<path d="M19 14c1.5-1.5 3-3.2 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.8'
             ' 0-3 .5-4.5 2-1.5-1.5-2.7-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 '
             '1.5 4 3 5.5l7 7z"/>',
    "capsule": '<path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 '
               '4.95 0 1 0 7 7zM8.5 8.5l7 7"/>',
    "microscope": '<path d="M6 18h8M3 22h18M14 22a7 7 0 1 0 0-14h-1M9 14h2'
                  'M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2zM12 6V3a1 1 0 0'
                  ' 0-1-1H9a1 1 0 0 0-1 1v3"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "close": '<path d="M18 6 6 18M6 6l12 12"/>',
    "chat": '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-4.9A8 8 0 1 1 21'
            ' 12z"/><path d="M8.5 12h.01M12 12h.01M15.5 12h.01"/>',
    "mic": '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 11a'
           '7 7 0 0 0 14 0M12 18v4M8 22h8"/>',
    "volume": '<path d="M11 5 6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1'
              ' 0 7M18.5 5.5a9 9 0 0 1 0 13"/>',
    "send": '<path d="M22 2 11 13M22 2l-7 20-4-9-9-4z"/>',
}
# Filled LinkedIn glyph; it is not a line icon, so it is kept apart.
LINKEDIN_SVG = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path '
    'd="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45'
    '-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 '
    '4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0'
    ' 1 1 0 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 '
    '1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24'
    ' .77 23.2 0 22.22 0z"/></svg>')

# Business navigation: (key, label, href, children).
B2B_NAV = [
    ("index", "Inicio", "index.html", []),
    ("soluciones", "Soluciones", "soluciones.html", [
        ("Todas las soluciones", "soluciones.html"),
        ("Complementos alimenticios", "soluciones.html#complementos"),
        ("Living biotherapeutics", "soluciones.html#living-biotherapeutics"),
        ("Optimización de bioprocesos", "soluciones.html#bioprocesos"),
        ("Agroambiental", "soluciones.html#agroambiental"),
    ]),
    ("pipeline", "Pipeline", "pipeline.html", []),
    ("mision", "Misión", "mision.html", []),
    ("equipo", "Sobre nosotros", "equipo.html", []),
    ("noticias", "Noticias", "noticias.html", []),
]
# Patients navigation: in-page anchors of pacientes.html.
B2C_NAV = [
    ("pacientes", "MycoRelax", "pacientes.html", []),
    ("encuesta", "Encuesta", "pacientes.html#encuesta", []),
    ("donar", "Donar", "pacientes.html#donar", []),
    ("investigacion", "Investigación", "pacientes.html#investigacion", []),
]

# Supporters shown in the marquee: (file, alt text, width, height).
SUPPORTERS = [
    ("uv.png", "Universitat de València", 160, 160),
    ("biotecmed.png", "BIOTECMED, Institut Universitari de Biotecnologia i "
     "Biomedicina", 380, 65),
    ("iata.png", "IATA-CSIC", 226, 127),
    ("i2sysbio.png", "I2SysBio, Instituto de Biología Integrativa de "
     "Sistemas", 180, 180),
    ("gva.png", "Generalitat Valenciana", 400, 167),
    ("uvempren.png", "UVemprén", 360, 88),
    ("bisce.png", "BISC-E, Biobased Innovation Student Challenge Europe",
     213, 160),
    ("ual.png", "Universidad de Almería", 170, 180),
    ("agrotecuv.png", "AgrotecUV", 400, 57),
]


@dataclass
class Page:
    """Metadata of one generated page.

    Attributes:
        file_name: Output file name, also the fragment name.
        title: Text of the <title> element.
        description: Meta description.
        audience: "b2b" for companies or "b2c" for patients.
        active: Key of the highlighted navigation item.
    """

    file_name: str
    title: str
    description: str
    audience: str
    active: str


PAGES = [
    Page("index.html",
         "Kyobac Labs | Patentes microbiológicas y bioinformática para "
         "empresas",
         "Kyobac Labs desarrolla cepas microbianas mejoradas sin "
         "modificación genética y soluciones bioinformáticas, y licencia su "
         "propiedad intelectual a empresas.", "b2b", "index"),
    Page("soluciones.html", "Soluciones | Kyobac Labs",
         "Complementos alimenticios, living biotherapeutics y optimización "
         "de bioprocesos: las soluciones de Kyobac Labs para empresas.",
         "b2b", "soluciones"),
    Page("pipeline.html", "Pipeline | Kyobac Labs",
         "Estado de los programas de Kyobac Labs abiertos a licencia.",
         "b2b", "pipeline"),
    Page("mision.html", "Misión | Kyobac Labs",
         "Misión, visión y forma de trabajar de Kyobac Labs.", "b2b",
         "mision"),
    Page("equipo.html", "Sobre nosotros | Kyobac Labs",
         "El equipo de Kyobac Labs y sus colaboradores científicos.", "b2b",
         "equipo"),
    Page("noticias.html", "Noticias | Kyobac Labs",
         "Premios, presencia en medios e hitos de Kyobac Labs.", "b2b",
         "noticias"),
    Page("empleo.html", "Trabaja con nosotros | Kyobac Labs",
         "Envía tu CV a Kyobac Labs si quieres trabajar en biotecnología "
         "microbiana y bioinformática.", "b2b", "empleo"),
    Page("aviso-legal.html", "Aviso legal | Kyobac Labs",
         "Aviso legal, condiciones de uso y propiedad intelectual e "
         "industrial del sitio web de Kyobac Labs.", "b2b", "legal"),
    Page("privacidad.html", "Política de privacidad | Kyobac Labs",
         "Cómo trata Kyobac Labs los datos personales conforme al RGPD y "
         "a la LOPDGDD.", "b2b", "legal"),
    Page("cookies.html", "Política de cookies | Kyobac Labs",
         "Uso de cookies y tecnologías similares en el sitio web de Kyobac "
         "Labs.", "b2b", "legal"),
    Page("pacientes.html", "MycoRelax · Pacientes | Kyobac Labs",
         "MycoRelax, el postbiótico en investigación de Kyobac Labs. "
         "Participa en la encuesta o apoya la investigación con una "
         "donación.", "b2c", "pacientes"),
]


def icon(name: str, extra: str = "") -> str:
    """Return an inline line-icon SVG.

    Args:
        name: Key of the icon in ICONS, or "linkedin" for the filled
            LinkedIn glyph.
        extra: Extra attributes for the <svg> element (ignored for
            "linkedin").

    Returns:
        SVG markup hidden from assistive technology.

    Raises:
        KeyError: If the icon name is unknown.
    """
    if name != "linkedin" and name not in ICONS:
        raise KeyError(f"Unknown icon: {name}")
    attributes = f" {extra}" if extra else ""
    if name == "linkedin":
        result = LINKEDIN_SVG
    else:
        result = (
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.6" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true"{attributes}>'
            f'{ICONS[name]}</svg>')
    return result


def render_nav(page: Page) -> str:
    """Build the main navigation list for the page's audience.

    Args:
        page: Page being generated.

    Returns:
        HTML of the <ul class="nav-list"> element.
    """
    items = B2B_NAV if page.audience == "b2b" else B2C_NAV
    lines = ['<ul class="nav-list">']
    for key, label, href, children in items:
        current = ' aria-current="page"' if key == page.active else ""
        if children:
            sub = "".join(f'<li><a href="{child_href}">{child_label}</a>'
                          f'</li>' for child_label, child_href in children)
            lines.append(
                f'            <li class="has-sub"><a href="{href}"{current}>'
                f'{label} {icon("chevron-down")}</a>'
                f'<ul class="subnav">{sub}</ul></li>')
        else:
            lines.append(f'            <li><a href="{href}"{current}>{label}'
                         f'</a></li>')
    lines.append("          </ul>")
    result = "\n".join(lines)
    return result


def render_header(page: Page) -> str:
    """Build the sticky header: logo plus a one-row card with the
    audience tabs, the navigation and the action buttons.

    Args:
        page: Page being generated.

    Returns:
        HTML of the <header> element.
    """
    is_b2b = page.audience == "b2b"
    theme = "" if is_b2b else " theme-light"
    logo = "logo_h_claro.png" if is_b2b else "logo_h_oscuro.png"
    b2b_current = ' aria-current="true"' if is_b2b else ""
    b2c_current = "" if is_b2b else ' aria-current="true"'
    if is_b2b:
        jobs_current = (' aria-current="page"' if page.active == "empleo"
                        else "")
        actions = (f'<a class="btn btn--line btn--small" href="empleo.html"'
                   f'{jobs_current}>Empleo</a>\n'
                   f'            <a class="btn btn--accent btn--small" '
                   f'href="index.html#contacto">Contacto</a>')
    else:
        actions = (f'<a class="btn btn--accent btn--small" '
                   f'href="{SURVEY_URL}" target="_blank" rel="noopener">'
                   f'Responder la encuesta</a>')
    result = f"""  <header class="site-header{theme}">
    <div class="header-row">
      <a class="brand" href="{'index.html' if is_b2b else 'pacientes.html'}" aria-label="Kyobac Labs, inicio">
        <img src="imagenes/{logo}" alt="Kyobac Labs" width="720" height="141">
      </a>
      <div class="header-card">
        <nav class="audience-bar" aria-label="Público">
          <ul class="audience-tabs">
            <li><a href="index.html"{b2b_current}>Empresas</a></li>
            <li><a href="pacientes.html"{b2c_current}>Pacientes</a></li>
          </ul>
        </nav>
        <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Abrir menú">
          {icon("menu", 'class="icon-menu"')}
          {icon("close", 'class="icon-close"')}
        </button>
        <nav id="site-nav" class="site-nav" aria-label="Principal">
          {render_nav(page)}
          <div class="nav-actions">
            {actions}
          </div>
        </nav>
      </div>
    </div>
  </header>"""
    return result


def render_supporters() -> str:
    """Build the "Apoyado por" band with a left-to-right logo marquee.

    The logo list is written twice; the copy is hidden from assistive
    technology and lets the CSS animation loop without a gap.

    Returns:
        HTML of the supporters <section>.
    """
    logos = "".join(
        f'<li><img src="imagenes/apoyos/blanco/{file_name}" alt="{alt}" '
        f'width="{width}" height="{height}" loading="lazy"></li>'
        for file_name, alt, width, height in SUPPORTERS)
    copy = re.sub(r'alt="[^"]*"', 'alt=""', logos)
    result = f"""  <section class="supporters" aria-labelledby="apoyos-titulo">
    <div class="container">
      <h2 id="apoyos-titulo" class="supporters-title">Apoyado <strong>por</strong></h2>
    </div>
    <div class="marquee">
      <div class="marquee-track">
        <ul class="logo-row">{logos}</ul>
        <ul class="logo-row" aria-hidden="true">{copy}</ul>
      </div>
    </div>
  </section>"""
    return result


def render_footer() -> str:
    """Build the multi-column site footer.

    Returns:
        HTML of the <footer> element.
    """
    result = f"""  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div>
          <h4>Soluciones</h4>
          <ul>
            <li><a href="soluciones.html#complementos">Complementos alimenticios</a></li>
            <li><a href="soluciones.html#living-biotherapeutics">Living biotherapeutics</a></li>
            <li><a href="soluciones.html#bioprocesos">Optimización de bioprocesos</a></li>
            <li><a href="soluciones.html#agroambiental">Agroambiental</a></li>
          </ul>
        </div>
        <div>
          <h4>Empresa</h4>
          <ul>
            <li><a href="pipeline.html">Pipeline</a></li>
            <li><a href="mision.html">Misión</a></li>
            <li><a href="equipo.html">Sobre nosotros</a></li>
            <li><a href="noticias.html">Noticias</a></li>
            <li><a href="empleo.html">Trabaja con nosotros</a></li>
          </ul>
        </div>
        <div>
          <h4>Pacientes</h4>
          <ul>
            <li><a href="pacientes.html">MycoRelax</a></li>
            <li><a href="pacientes.html#encuesta">Encuesta</a></li>
            <li><a href="pacientes.html#donar">Donaciones</a></li>
          </ul>
        </div>
        <div>
          <h4>Contacto</h4>
          <ul>
            <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
            <li><a href="{LINKEDIN}" target="_blank" rel="noopener">LinkedIn</a></li>
            <li>Valencia (España)</li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <img src="imagenes/logo_claro.png" alt="Kyobac Labs" width="640" height="241" loading="lazy">
        <span>© <span class="js-year">2026</span> Kyobac Labs. Todos los derechos reservados. Datos preclínicos: ningún producto de Kyobac Labs está autorizado para su venta.</span>
        <nav class="legal-links" aria-label="Información legal">
          <a href="aviso-legal.html">Aviso legal</a>
          <a href="privacidad.html">Privacidad</a>
          <a href="cookies.html">Cookies</a>
        </nav>
      </div>
    </div>
  </footer>"""
    return result


def render_assistant(page: Page) -> str:
    """Build the chat widget of Clara, the website assistant.

    The panel starts hidden; js/main.js opens it, talks to the Worker at
    CLARA_ENDPOINT and shows the microphone and speaker buttons only when
    the browser supports them. Without JavaScript the CSS hides it all.

    Args:
        page: Page being generated.

    Returns:
        HTML of the widget, or an empty string if CLARA_ENDPOINT is empty.
    """
    theme = "" if page.audience == "b2b" else " theme-light"
    result = ""
    if CLARA_ENDPOINT:
        result = f"""  <div class="assistant{theme}" data-endpoint="{escape(CLARA_ENDPOINT)}" data-contact="{EMAIL}">
    <button class="assistant-launcher" type="button" aria-expanded="false" aria-controls="assistant-panel">
      {icon("chat")}<span>Pregunta a Clara</span>
    </button>
    <section id="assistant-panel" class="assistant-panel" role="dialog" aria-labelledby="assistant-title" hidden>
      <div class="assistant-head">
        <div class="assistant-id">
          <h2 id="assistant-title">Clara</h2>
          <p>Asistente con inteligencia artificial</p>
        </div>
        <button class="assistant-icon js-assistant-speak" type="button" aria-pressed="false" aria-label="Leer las respuestas en voz alta" title="Leer las respuestas en voz alta" hidden>{icon("volume")}</button>
        <button class="assistant-icon js-assistant-close" type="button" aria-label="Cerrar el chat" title="Cerrar">{icon("close")}</button>
      </div>
      <p class="assistant-notice">Estás hablando con una inteligencia artificial. Clara responde solo con la información de esta web, puede equivocarse y no da consejo médico. No compartas datos personales ni de salud. <a href="privacidad.html#clara">Más información</a></p>
      <div class="assistant-log" role="log" aria-live="polite">
        <p class="assistant-msg assistant-msg--bot">Hola, soy Clara. ¿En qué puedo ayudarte?</p>
      </div>
      <form class="assistant-form">
        <label class="visually-hidden" for="assistant-input">Escribe tu pregunta</label>
        <textarea id="assistant-input" rows="1" maxlength="600" placeholder="Escribe tu pregunta…" autocomplete="off"></textarea>
        <button class="assistant-icon js-assistant-mic" type="button" aria-pressed="false" aria-label="Hablar" title="Hablar" hidden>{icon("mic")}</button>
        <button class="assistant-send" type="submit" aria-label="Enviar" title="Enviar">{icon("send")}</button>
      </form>
    </section>
  </div>"""
    return result


def render_page(page: Page, main_html: str) -> str:
    """Wrap a <main> fragment with the shared document skeleton.

    Args:
        page: Page being generated.
        main_html: Content of the <main> element.

    Returns:
        Complete HTML document.
    """
    is_b2c = page.audience == "b2c"
    body_class = ' class="b2c"' if is_b2c else ""
    main_class = ' class="theme-light"' if is_b2c else ""
    main_html = ICON_PATTERN.sub(lambda match: icon(match.group(1)),
                                 main_html.rstrip())
    result = f"""<!DOCTYPE html>
<!--
  {page.file_name} — Kyobac Labs website. Generated by _src/build.py; edit
  _src/paginas/{page.file_name} instead of this file.
  Version: {VERSION} · Author: Adrian Berenguer-Agustí (I2SysBio-CSIC) · Date: {BUILD_DATE}
-->
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page.title}</title>
  <meta name="description" content="{page.description}">
  <meta name="theme-color" content="#171d24">
  <link rel="preload" href="fonts/mulish-latin.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="css/style.css">
  <script>document.documentElement.classList.add("js");</script>
  <script src="js/main.js" defer></script>
  <script data-goatcounter="https://kyobac.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</head>
<body{body_class}>
  <a class="skip-link" href="#main">Saltar al contenido</a>

{render_header(page)}

  <main id="main"{main_class}>
{main_html}
  </main>

{render_supporters()}

{render_footer()}

{render_assistant(page)}
</body>
</html>
"""
    return result


class _TextExtractor(HTMLParser):
    """Collect the readable text of a <main> fragment for Clara.

    Headings become lines starting with "#", block elements become line
    breaks, external links keep their address and the pending-text
    placeholders (class "placeholder") are dropped.
    """

    # Elements that start a new line in the extracted text.
    BLOCKS = {"p", "li", "div", "section", "article", "header", "tr", "br",
              "dd", "dt", "figcaption", "blockquote", "table"}
    # Heading tags and the Markdown-like prefix they receive.
    HEADINGS = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### "}
    # Elements whose content is never text for the reader.
    SKIPPED = {"script", "style", "svg", "template"}
    # Void elements: they never get an end tag.
    VOID = {"img", "br", "hr", "input", "meta", "link", "source", "wbr"}

    def __init__(self) -> None:
        """Start with no text, no open skipped element and no links."""
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0
        self.links: list[str] = []

    def handle_starttag(self, tag: str,
                        attrs: list[tuple[str, str | None]]) -> None:
        """Open a heading, block, link or skipped element.

        Args:
            tag: Lower-case tag name.
            attrs: Attribute name and value pairs of the tag.
        """
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if self.skip_depth:
            if tag not in self.VOID:
                self.skip_depth += 1
        elif tag in self.SKIPPED or "placeholder" in classes:
            self.skip_depth = 1
        elif tag in self.HEADINGS:
            self.parts.append("\n\n" + self.HEADINGS[tag])
        elif tag in self.BLOCKS:
            self.parts.append("\n")
        elif tag == "a":
            href = attributes.get("href") or ""
            external = href.startswith(("http", "mailto:", "tel:"))
            self.links.append(href if external else "")

    def handle_endtag(self, tag: str) -> None:
        """Close an element, appending a link address if it has one.

        Args:
            tag: Lower-case tag name.
        """
        if self.skip_depth:
            self.skip_depth -= 1
        elif tag in self.HEADINGS:
            self.parts.append("\n")
        elif tag == "a" and self.links:
            href = self.links.pop()
            if href:
                # Mail and phone links keep only the address, without
                # the scheme or a prefilled subject.
                address = (href.split(":", 1)[1].split("?", 1)[0]
                           if href.startswith(("mailto:", "tel:")) else href)
                self.parts.append(f" ({address})")

    def handle_data(self, data: str) -> None:
        """Keep text outside skipped elements, collapsing whitespace.

        Args:
            data: Text between tags.
        """
        if not self.skip_depth:
            self.parts.append(re.sub(r"\s+", " ", data))


def page_text(main_html: str) -> str:
    """Extract the readable text of a <main> fragment.

    Args:
        main_html: Content of the page's <main> element.

    Returns:
        Plain text with one block per line and no blank-line runs.
    """
    extractor = _TextExtractor()
    extractor.feed(ICON_PATTERN.sub("", main_html))
    extractor.close()
    lines = (line.strip() for line in "".join(extractor.parts).split("\n"))
    text = "\n".join(re.sub(r" {2,}", " ", line) for line in lines if line)
    result = re.sub(r"\n(#+ )", r"\n\n\1", text).strip()
    return result


def knowledge_appendix() -> str:
    """Return the facts Clara needs that are outside the page bodies.

    Returns:
        Plain text on contact details, legal pages and Clara herself.
    """
    result = f"""=== Información general (cabecera, pie y páginas legales) ===
La web tiene dos zonas: Empresas (licencias de patentes y bioinformática) y Pacientes (MycoRelax: encuesta y donaciones).
Contacto: correo {EMAIL}; LinkedIn ({LINKEDIN}); Kyobac Labs está en Valencia (España). Para contactar como empresa, usa el botón Contacto de la web o escribe al correo.
Encuesta para pacientes: {SURVEY_URL}
Empleo: la página Trabaja con nosotros (empleo.html) explica cómo enviar el CV.
Aviso del pie de página: datos preclínicos; ningún producto de Kyobac Labs está autorizado para su venta.
Información legal: Aviso legal (aviso-legal.html), Política de privacidad (privacidad.html) y Política de cookies (cookies.html). La web no usa cookies; mide las visitas con GoatCounter, sin cookies y sin guardar la IP. Para ejercer derechos de protección de datos, escribe a {EMAIL}.
Sobre Clara: es un asistente de inteligencia artificial de la web. Usa un modelo de lenguaje de Cloudflare Workers AI, responde solo con la información de esta web y no guarda las conversaciones. La entrada por voz la transcribe el navegador (en algunos navegadores, en servidores de su proveedor, como Google o Apple). Más detalles en la Política de privacidad."""
    return result


def write_knowledge_base(page_html: dict[str, str]) -> None:
    """Write Clara's knowledge base from the public page fragments.

    Args:
        page_html: Content of <main> for each page, keyed by file name.

    Raises:
        KeyError: If a page in KNOWLEDGE_PAGES is not in PAGES.
    """
    titles = {page.file_name: page.title for page in PAGES}
    sections = [f"=== Página: {titles[name]} ({name}) ===\n"
                f"{page_text(page_html[name])}"
                for name in KNOWLEDGE_PAGES]
    sections.append(knowledge_appendix())
    CLARA_DIR.mkdir(exist_ok=True)
    KNOWLEDGE_FILE.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Wrote {KNOWLEDGE_FILE.relative_to(SITE_DIR)}")


def main() -> None:
    """Generate every page listed in PAGES into SITE_DIR, then Clara's
    knowledge base."""
    missing = [page.file_name for page in PAGES
               if not (PAGES_DIR / page.file_name).is_file()]
    if missing:
        sys.exit(f"Missing page fragments in {PAGES_DIR}: "
                 f"{', '.join(missing)}")
    page_html = {}
    for page in PAGES:
        main_html = (PAGES_DIR / page.file_name).read_text(encoding="utf-8")
        page_html[page.file_name] = main_html
        output = render_page(page, main_html)
        (SITE_DIR / page.file_name).write_text(output, encoding="utf-8")
        print(f"Wrote {page.file_name}")
    write_knowledge_base(page_html)


if __name__ == "__main__":
    main()
