#!/usr/bin/env python3
# ruff: noqa: E501, RUF001
"""Build the self-contained bilingual documentation site from Markdown."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "site" / "index.html"

NAV_BY_LANGUAGE = {
    "de": [
        ("Start", [("index", "Übersicht")]),
        (
            "Erste Schritte",
            [
                ("installation", "Installation"),
                ("configuration", "Konfiguration"),
                ("how-it-works", "Funktionsweise"),
            ],
        ),
        (
            "Funktionen",
            [
                ("supported-syntax", "Unterstützte Syntax"),
                ("sensor", "Result-Sensor"),
                ("services", "Aktion scan_now"),
                ("events", "Events"),
                ("notifications", "Benachrichtigungen"),
                ("ignore-list", "Ausschlüsse"),
                ("diagnostics", "Diagnostik"),
            ],
        ),
        (
            "Referenz",
            [
                ("limitations", "Bekannte Grenzen"),
                ("troubleshooting", "Fehlerbehebung"),
                ("requirements", "Anforderungen"),
            ],
        ),
    ],
    "en": [
        ("Start", [("index", "Overview")]),
        (
            "Getting started",
            [
                ("installation", "Installation"),
                ("configuration", "Configuration"),
                ("how-it-works", "How it works"),
            ],
        ),
        (
            "Features",
            [
                ("supported-syntax", "Supported syntax"),
                ("sensor", "Result sensor"),
                ("services", "scan_now action"),
                ("events", "Events"),
                ("notifications", "Notifications"),
                ("ignore-list", "Exclusions"),
                ("diagnostics", "Diagnostics"),
            ],
        ),
        (
            "Reference",
            [
                ("limitations", "Known limitations"),
                ("troubleshooting", "Troubleshooting"),
                ("requirements", "Requirements"),
            ],
        ),
    ],
}

UI = {
    "de": {
        "menu": "Menü",
        "open": "Öffnen",
        "toc": "Auf dieser Seite",
        "search": "Dokumentation filtern",
        "light": "Hell",
        "dark": "Dunkel",
    },
    "en": {
        "menu": "Menu",
        "open": "Open",
        "toc": "On this page",
        "search": "Filter documentation",
        "light": "Light",
        "dark": "Dark",
    },
}


def inline(text: str, language: str) -> str:
    """Render the small inline Markdown subset used by these docs."""
    escaped = html.escape(text, quote=False)
    placeholders: list[str] = []

    def protect_code(match: re.Match[str]) -> str:
        placeholders.append(f"<code>{match.group(1)}</code>")
        return f"\x00CODE{len(placeholders) - 1}\x00"

    escaped = re.sub(r"`([^`]+)`", protect_code, escaped)

    def render_link(match: re.Match[str]) -> str:
        label, target = match.group(1), html.unescape(match.group(2))
        local = re.fullmatch(r"\./([a-z0-9-]+)\.md", target)
        if local:
            slug = local.group(1)
            return f'<a href="#{language}/{slug}" data-page-link="{slug}">{label}</a>'
        return f'<a href="{html.escape(target, quote=True)}">{label}</a>'

    escaped = re.sub(r"\[([^]]+)]\(([^)]+)\)", render_link, escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    for index, value in enumerate(placeholders):
        escaped = escaped.replace(f"\x00CODE{index}\x00", value)
    return escaped


def is_table_separator(line: str) -> bool:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def render_markdown(markdown: str, language: str) -> str:
    """Render headings, paragraphs, code, tables, lists and blockquotes."""
    lines = markdown.splitlines()
    output: list[str] = []
    paragraph: list[str] = []
    index = 0

    def flush_paragraph() -> None:
        if paragraph:
            output.append(
                f"<p>{inline(' '.join(part.strip() for part in paragraph), language)}</p>"
            )
            paragraph.clear()

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            code_language = stripped[3:].strip()
            code: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code.append(lines[index])
                index += 1
            class_name = (
                f' class="language-{html.escape(code_language)}"'
                if code_language
                else ""
            )
            output.append(
                f"<pre><code{class_name}>{html.escape(chr(10).join(code))}</code></pre>"
            )
        elif re.match(r"^#{1,3} ", stripped):
            flush_paragraph()
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            output.append(f"<h{level}>{inline(text, language)}</h{level}>")
        elif (
            index + 1 < len(lines)
            and "|" in line
            and is_table_separator(lines[index + 1])
        ):
            flush_paragraph()
            headers = [cell.strip() for cell in line.strip().strip("|").split("|")]
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                rows.append(
                    [
                        cell.strip()
                        for cell in lines[index].strip().strip("|").split("|")
                    ]
                )
                index += 1
            head = "".join(f"<th>{inline(cell, language)}</th>" for cell in headers)
            body = "".join(
                "<tr>"
                + "".join(f"<td>{inline(cell, language)}</td>" for cell in row)
                + "</tr>"
                for row in rows
            )
            output.append(
                f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
            )
            continue
        elif re.match(r"^- ", stripped):
            flush_paragraph()
            items: list[str] = []
            while index < len(lines) and re.match(r"^- ", lines[index].strip()):
                items.append(lines[index].strip()[2:])
                index += 1
            output.append(
                "<ul>"
                + "".join(f"<li>{inline(item, language)}</li>" for item in items)
                + "</ul>"
            )
            continue
        elif re.match(r"^\d+\. ", stripped):
            flush_paragraph()
            items = []
            start_number = int(stripped.split(".", 1)[0])
            while index < len(lines) and re.match(r"^\d+\. ", lines[index].strip()):
                items.append(re.sub(r"^\d+\. ", "", lines[index].strip()))
                index += 1
            start_attribute = f' start="{start_number}"' if start_number != 1 else ""
            output.append(
                f"<ol{start_attribute}>"
                + "".join(f"<li>{inline(item, language)}</li>" for item in items)
                + "</ol>"
            )
            continue
        elif stripped.startswith("> "):
            flush_paragraph()
            output.append(f"<blockquote>{inline(stripped[2:], language)}</blockquote>")
        elif stripped == "---":
            flush_paragraph()
            output.append("<hr>")
        elif not stripped:
            flush_paragraph()
        else:
            paragraph.append(line)
        index += 1

    flush_paragraph()
    return "\n".join(output)


def all_pages(language: str) -> list[tuple[str, str]]:
    return [item for _group, items in NAV_BY_LANGUAGE[language] for item in items]


def main() -> None:
    page_data: dict[str, dict[str, str]] = {}
    nav_data: dict[str, list[dict[str, object]]] = {}
    for language, navigation in NAV_BY_LANGUAGE.items():
        for slug, nav_title in all_pages(language):
            source = ROOT / language / f"{slug}.md"
            markdown = source.read_text(encoding="utf-8")
            rendered = render_markdown(markdown, language)
            title_match = re.search(r"^# (.+)$", markdown, re.MULTILINE)
            title = title_match.group(1) if title_match else nav_title
            page_data[f"{language}/{slug}"] = {"title": title, "html": rendered}

        cards = "".join(
            f'<a class="card" href="#{language}/{slug}" data-page-link="{slug}">'
            f"<strong>{html.escape(title)}</strong><span>{UI[language]['open']}</span></a>"
            for slug, title in all_pages(language)
            if slug != "index"
        )
        heading = "Dokumentation" if language == "de" else "Documentation"
        key = f"{language}/index"
        page_data[key]["html"] = page_data[key]["html"].replace(
            f"<h2>{heading}</h2>",
            f'<h2>{heading}</h2><div class="card-grid">{cards}</div>',
            1,
        )
        nav_data[language] = [
            {
                "group": group,
                "items": [{"slug": slug, "title": title} for slug, title in items],
            }
            for group, items in navigation
        ]

    payload = {
        "pages": page_data,
        "navigation": nav_data,
        "ui": UI,
    }
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    document = TEMPLATE.replace("__DATA__", data_json)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(document, encoding="utf-8")
    (OUTPUT.parent / ".nojekyll").write_text("", encoding="utf-8")
    print(
        f"Wrote {OUTPUT} from {len(page_data)} Markdown pages "
        f"in {len(NAV_BY_LANGUAGE)} languages"
    )


TEMPLATE = r"""<!doctype html>
<html lang="de" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Template Entity Checker – Dokumentation</title>
<style>
:root{--bg:#fff;--panel:#fafafa;--text:#171717;--muted:#666;--border:#e5e7eb;--accent:#0070f3;--code:#f3f4f6;--side:280px;--toc:230px}
html[data-theme=dark]{--bg:#0d1117;--panel:#161b22;--text:#e6edf3;--muted:#9da7b3;--border:#30363d;--accent:#58a6ff;--code:#161b22}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.sidebar{position:fixed;inset:0 auto 0 0;width:var(--side);border-right:1px solid var(--border);background:var(--panel);padding:24px 18px;overflow:auto}.brand{font-weight:750;font-size:18px;margin-bottom:18px}.search{width:100%;padding:9px 11px;border:1px solid var(--border);border-radius:8px;background:var(--bg);color:var(--text);margin-bottom:18px}.nav-group{margin:18px 0}.nav-group h2{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 8px 6px}.nav-group a{display:block;color:var(--muted);padding:6px 10px;border-left:2px solid transparent;border-radius:0 7px 7px 0}.nav-group a.active{color:var(--accent);border-left-color:var(--accent);background:color-mix(in srgb,var(--accent) 9%,transparent);font-weight:650}
.toolbar{position:fixed;right:18px;top:14px;z-index:7;display:flex;gap:8px}.segmented{display:flex;border:1px solid var(--border);border-radius:9px;overflow:hidden;background:var(--bg)}.segmented button{border:0;background:transparent;color:var(--muted);padding:7px 10px;cursor:pointer}.segmented button.active{background:var(--accent);color:white}.mobile-menu{display:none;border:1px solid var(--border);border-radius:9px;background:var(--bg);color:var(--text);padding:7px 10px;cursor:pointer}.mobile-overlay{display:none}
.shell{margin-left:var(--side);padding:58px calc(var(--toc) + 54px) 80px 54px}.content{max-width:860px;margin:auto}.content h1{font-size:38px;line-height:1.18;margin:0 0 25px;letter-spacing:-.025em}.content h2{font-size:25px;margin:44px 0 14px}.content h3{font-size:18px;margin:30px 0 10px}.content p{margin:12px 0}.content code{background:var(--code);color:#d6336c;padding:.16em .38em;border-radius:5px;font:13px ui-monospace,SFMono-Regular,Consolas,monospace}.content pre{background:var(--code);border:1px solid var(--border);padding:16px;border-radius:10px;overflow:auto}.content pre code{padding:0;color:var(--text);background:none}.content blockquote{margin:20px 0;padding:12px 16px;border-left:3px solid var(--accent);background:var(--panel);color:var(--muted)}.content li{margin:5px 0}.table-wrap{overflow:auto;margin:18px 0}table{width:100%;border-collapse:collapse}th,td{text-align:left;vertical-align:top;border:1px solid var(--border);padding:9px 11px}th{background:var(--panel)}hr{border:0;border-top:1px solid var(--border)}
.card-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:18px 0 26px}.card{border:1px solid var(--border);border-radius:11px;padding:16px;color:var(--text);display:flex;justify-content:space-between;align-items:center}.card span{color:var(--muted);font-size:12px}.card:hover{border-color:var(--accent);box-shadow:0 5px 18px rgba(0,0,0,.08);text-decoration:none}
.toc{position:fixed;right:25px;top:70px;width:var(--toc);max-height:calc(100vh - 90px);overflow:auto;border-left:1px solid var(--border);padding-left:16px}.toc strong{font-size:12px}.toc a{display:block;color:var(--muted);font-size:13px;padding:4px 0}.toc a:hover{color:var(--accent)}
@media(max-width:1100px){.shell{padding-right:45px}.toc{display:none}}@media(max-width:768px){.sidebar{z-index:6;transform:translateX(-105%);transition:transform .2s ease;box-shadow:8px 0 24px rgba(0,0,0,.18)}.sidebar.open{transform:translateX(0)}.mobile-menu{display:block}.mobile-overlay.open{display:block;position:fixed;inset:0;z-index:5;border:0;background:rgba(0,0,0,.48)}.shell{margin-left:0;padding:70px 20px}.content h1{font-size:32px}.card-grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<aside class="sidebar"><div class="brand">Template Entity Checker</div><input id="search" class="search" type="search"><nav id="navigation"></nav></aside>
<button id="mobile-overlay" class="mobile-overlay" onclick="closeMobileMenu()" aria-label="Close menu"></button>
<div class="toolbar">
  <button id="menu-toggle" class="mobile-menu" onclick="toggleMobileMenu()" aria-expanded="false">Menu</button>
  <div class="segmented" aria-label="Language"><button id="lang-de" onclick="switchLanguage('de')">DE</button><button id="lang-en" onclick="switchLanguage('en')">EN</button></div>
  <div class="segmented" aria-label="Theme"><button id="light" onclick="setTheme('light')">Light</button><button id="dark" onclick="setTheme('dark')">Dark</button></div>
</div>
<div class="shell"><main id="content" class="content"></main></div><aside id="toc" class="toc"></aside>
<script>
const data=__DATA__,pages=data.pages,navigation=data.navigation,ui=data.ui;
let currentLanguage='en',currentSlug='index';
function slugify(value){return value.toLowerCase().replace(/ß/g,'ss').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')}
function filterNavigation(query){const q=query.toLowerCase();document.querySelectorAll('.nav-group').forEach(group=>{let visible=0;group.querySelectorAll('a').forEach(a=>{const show=a.textContent.toLowerCase().includes(q);a.style.display=show?'block':'none';visible+=show});group.style.display=visible?'block':'none'})}
function closeMobileMenu(){document.querySelector('.sidebar').classList.remove('open');document.getElementById('mobile-overlay').classList.remove('open');document.getElementById('menu-toggle').setAttribute('aria-expanded','false')}
function toggleMobileMenu(){const open=!document.querySelector('.sidebar').classList.contains('open');document.querySelector('.sidebar').classList.toggle('open',open);document.getElementById('mobile-overlay').classList.toggle('open',open);document.getElementById('menu-toggle').setAttribute('aria-expanded',String(open))}
function renderNavigation(language){document.getElementById('navigation').innerHTML=navigation[language].map(group=>`<section class="nav-group"><h2>${group.group}</h2>${group.items.map(item=>`<a href="#${language}/${item.slug}" data-page="${item.slug}">${item.title}</a>`).join('')}</section>`).join('');const search=document.getElementById('search');search.placeholder=ui[language].search;filterNavigation(search.value);document.querySelectorAll('#navigation a').forEach(a=>a.addEventListener('click',closeMobileMenu))}
function loadPage(language,slug,section=null){const key=`${language}/${slug}`;if(!pages[key]){language='en';slug='index'}currentLanguage=language;currentSlug=slug;localStorage.setItem('tec-doc-language',language);document.documentElement.lang=language;renderNavigation(language);document.getElementById('menu-toggle').textContent=ui[language].menu;document.getElementById('light').textContent=ui[language].light;document.getElementById('dark').textContent=ui[language].dark;const page=pages[`${language}/${slug}`];document.title=page.title+' – Template Entity Checker';const content=document.getElementById('content');content.innerHTML=page.html;document.querySelectorAll('[data-page]').forEach(a=>a.classList.toggle('active',a.dataset.page===slug));content.querySelectorAll('[data-page-link]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();location.hash=`${language}/${a.dataset.pageLink}`}));const headings=[...content.querySelectorAll('h2')];headings.forEach((h,i)=>h.id=slugify(h.textContent)||'section-'+i);document.getElementById('toc').innerHTML=`<strong>${ui[language].toc}</strong>`+headings.map(h=>`<a href="#${language}/${slug}:${h.id}">${h.textContent}</a>`).join('');document.querySelectorAll('[id^="lang-"]').forEach(b=>b.classList.toggle('active',b.id===`lang-${language}`));closeMobileMenu();if(section){document.getElementById(section)?.scrollIntoView({behavior:'instant',block:'start'})}else{window.scrollTo(0,0)}}
function route(){const [path,section]=location.hash.slice(1).split(':',2);if(path.includes('/')){const [language,slug]=path.split('/',2);loadPage(language,slug,section||null)}else{const saved=localStorage.getItem('tec-doc-language');const detected=navigator.language.toLowerCase().startsWith('de')?'de':'en';const language=saved&&navigation[saved]?saved:detected;location.replace(`#${language}/index`)}}
function switchLanguage(language){document.getElementById('search').value='';const section=location.hash.slice(1).split(':',2)[1]||null;let targetSection=null;if(section){const headings=[...document.querySelectorAll('#content h2')];const index=headings.findIndex(h=>h.id===section);const targetPage=pages[`${language}/${currentSlug}`];if(index>=0&&targetPage){const template=document.createElement('template');template.innerHTML=targetPage.html;const targetHeading=template.content.querySelectorAll('h2')[index];if(targetHeading)targetSection=slugify(targetHeading.textContent)}}location.hash=`${language}/${currentSlug}${targetSection?`:${targetSection}`:''}`}
function setTheme(theme){document.documentElement.dataset.theme=theme;localStorage.setItem('tec-doc-theme',theme);document.querySelectorAll('#light,#dark').forEach(b=>b.classList.toggle('active',b.id===theme))}
document.getElementById('search').addEventListener('input',e=>filterNavigation(e.target.value));window.addEventListener('hashchange',route);setTheme(localStorage.getItem('tec-doc-theme')||'light');route();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
