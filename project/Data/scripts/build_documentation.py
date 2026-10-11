"""Build the offline documentation using only Python's standard library.

Supports the Markdown blocks used in README_DATA_METHODOLOGY.md. Raw HTML is
escaped. Unsupported blocks fail rather than silently losing documentation.
"""
from html import escape
from pathlib import Path
import re

DATA = Path(__file__).resolve().parents[1]


def inline(value):
    tokens = []

    def protect(html):
        tokens.append(html)
        return f"\x00{len(tokens) - 1}\x00"

    value = re.sub(r"`([^`]+)`", lambda m: protect(f"<code>{escape(m[1])}</code>"), value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: protect(f'<a href="{escape(m[2], quote=True)}">{inline(m[1])}</a>'), value)
    value = escape(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    return re.sub(r"\x00(\d+)\x00", lambda m: tokens[int(m[1])], value)


def slug(value):
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def render(source):
    lines = source.splitlines()
    output, contents = [], []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("```"):
            language = line[3:].strip()
            start = index + 1
            index = start
            while index < len(lines) and not lines[index].startswith("```"):
                index += 1
            if index == len(lines):
                raise ValueError("Unclosed fenced code block")
            label = "PowerShell" if language == "powershell" else "Formula / definition"
            code = escape("\n".join(lines[start:index]))
            output.append(f'<div class="code-block"><div class="code-label">{label}</div><pre tabindex="0"><code>{code}</code></pre></div>')
            index += 1
            continue
        heading = re.match(r"^(#{1,3}) (.+)$", line)
        if heading:
            level, title = len(heading[1]), heading[2]
            anchor = slug(title)
            if level == 1:
                index += 1
                continue
            if level == 2:
                if contents:
                    output.append("</section>")
                contents.append((anchor, title))
                output.append(f'<section id="{anchor}" aria-labelledby="heading-{anchor}">')
            else:
                output.append(f'<span id="{anchor}"></span>')
            output.append(f'<h{level} id="heading-{anchor}">{inline(title)} <a class="anchor" href="#{anchor}" aria-label="Link to {escape(title, quote=True)}">#</a></h{level}>')
            index += 1
            continue
        if line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                rows.append([cell.strip() for cell in lines[index].strip().strip("|").split("|")])
                index += 1
            if len(rows) < 2 or not all(re.fullmatch(r":?-+:?", cell) for cell in rows[1]):
                raise ValueError("Table must include a separator row")
            if any(len(row) != len(rows[0]) for row in rows):
                raise ValueError("Inconsistent table widths")
            header = "".join(f'<th scope="col">{inline(cell)}</th>' for cell in rows[0])
            body = "".join("<tr>" + "".join(f"<td>{inline(cell)}</td>" for cell in row) + "</tr>" for row in rows[2:])
            output.append(f'<div class="table-scroll" tabindex="0" role="region" aria-label="{escape(rows[0][0], quote=True)} table"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>')
            continue
        if line.startswith("- "):
            items = []
            while index < len(lines) and lines[index].startswith("- "):
                item = lines[index][2:]
                index += 1
                while index < len(lines) and lines[index].startswith("  ") and not lines[index].startswith("  - "):
                    item += " " + lines[index].strip()
                    index += 1
                items.append(f"<li>{inline(item)}</li>")
            output.append("<ul>" + "".join(items) + "</ul>")
            continue
        if re.match(r"^(>|#{4}|\d+\. |\s{2,}- )", line):
            raise ValueError(f"Unsupported Markdown block: {line}")
        paragraph = []
        while index < len(lines) and lines[index].strip():
            if lines[index].startswith(("#", "```", "|", "- ")):
                break
            paragraph.append(lines[index])
            index += 1
        output.append("<p>" + inline(" ".join(paragraph)) + "</p>")
    if contents:
        output.append("</section>")
    return "\n".join(output), contents


def main():
    source = (DATA / "README_DATA_METHODOLOGY.md").read_text(encoding="utf-8")
    body, contents = render(source)
    links = "".join(f'<li><a href="#{anchor}">{escape(title)}</a></li>' for anchor, title in contents)
    page = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Kew data relationships, formulas, synthetic labels, quality, validation and reproducibility for the London v3 simulation.">
  <title>Kew · Data methodology</title>
  <link rel="stylesheet" href="documentation.css">
</head>
<body id="top">
  <a class="skip-link" href="#documentation">Skip to documentation</a>
  <header class="site-header"><a class="brand" href="#top">kew<span>Data documentation</span></a><a class="source-link" href="README_DATA_METHODOLOGY.md">Markdown source ↗</a></header>
  <div class="layout">
    <aside class="sidebar"><details open><summary>On this page</summary><nav aria-label="Section index"><ol>{links}</ol></nav></details><p class="sidebar-note">Public references.<br>Synthetic household records.<br>Reproducible methods.</p></aside>
    <main id="documentation">
      <div class="hero"><p class="eyebrow">Kew / London simulation v3</p><h1>Understand the data.<br>Trace every assumption.</h1><p class="hero-description">Data relationships, derived formulas, label generation, quality, validation and reproducibility.</p><div class="stats" aria-label="Dataset summary"><div><strong>2,000</strong><span>synthetic properties</span></div><div><strong>24,000</strong><span>monthly readings</span></div><div><strong>74</strong><span>documented CSV fields</span></div></div><p class="notice">Illustrative simulation informed by published statistics. These records are not observed homes, transaction prices or measured energy readings.</p></div>
      <article>{body}</article>
      <footer>Generated from <a href="README_DATA_METHODOLOGY.md">the methodology README</a>. <a href="#top">Back to top ↑</a></footer>
    </main>
  </div>
</body>
</html>
'''
    (DATA / "index.html").write_text(page, encoding="utf-8", newline="\n")
    print(f"Built Data/index.html: {len(contents)} indexed sections")


if __name__ == "__main__":
    main()
