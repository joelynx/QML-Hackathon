"""Build QML_Hackathon_Solution_Description.pdf from docs/report/report.html with headless Chrome (or Edge).

Numbers the sections and figures, resolves the section and figure references, writes the table of contents,
prints once to find the page of every heading (from the PDF's named destinations), then prints again with
the page numbers filled in. Figures come from docs/figures/ (scripts/make_figure.py, scripts/make_report_figures.py).

    python scripts/build_report.py [--browser PATH]      (from the project root)
"""
import argparse
import os
import re
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "report", "report.html")
TMP = os.path.join(ROOT, "docs", "report", "_build.html")  # next to the source, so relative figure paths resolve
OUT = os.path.join(ROOT, "QML_Hackathon_Solution_Description.pdf")
BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chromium-browser", "msedge",
]
HEAD = re.compile(r'<h([23])([^>]*)>(.*?)</h\1>', re.S)


def find_browser(explicit):
    for cand in ([explicit] if explicit else BROWSERS):
        if cand and (os.path.isfile(cand) or shutil.which(cand)):
            return cand if os.path.isfile(cand) else shutil.which(cand)
    raise SystemExit("no Chrome/Chromium/Edge found; pass --browser")


def number(src):
    """Return (html, headings) with section numbers and figure numbers filled in."""
    heads, n2, n3 = [], 0, 0

    def head(m):
        nonlocal n2, n3
        lvl, attrs, body = m.group(1), m.group(2), m.group(3)
        hid = re.search(r'id="([^"]+)"', attrs).group(1)
        num = ""
        if "nonum" not in attrs:
            if lvl == "2":
                n2, n3 = n2 + 1, 0
                num = str(n2)
            else:
                n3 += 1
                num = f"{n2}.{n3}"
        heads.append((lvl, hid, num, body.strip()))
        lead = f'<span class="secnum">{num}</span>' if num else ""
        return f"<h{lvl}{attrs}>{lead}{body}</h{lvl}>"

    html = HEAD.sub(head, src)
    secnum = {hid: num for _, hid, num, _ in heads}
    fignum = {}

    def fig(m):
        fignum[m.group(1)] = str(len(fignum) + 1)
        return m.group(0).replace('<span class="fignumv"></span>', fignum[m.group(1)])

    html = re.sub(r'<figure id="([^"]+)".*?</figure>', fig, html, flags=re.S)
    html = re.sub(r'<span class="secref" data-ref="([^"]+)"></span>', lambda m: secnum[m.group(1)], html)
    html = re.sub(r'<span class="figref" data-ref="([^"]+)"></span>', lambda m: fignum[m.group(1)], html)
    return html, heads


def toc(heads, pages):
    rows = ['<nav class="toc"><div class="tochead">Contents</div><ol>']
    for lvl, hid, num, body in heads:
        title = re.sub(r"<[^>]+>", "", body)
        rows.append(f'<li class="l{lvl}"><a class="row" href="#{hid}"><span class="num">{num}</span>'
                    f'<span class="t">{title}</span><span class="dots"></span>'
                    f'<span class="pg">{pages.get(hid, "00")}</span></a></li>')
    rows.append("</ol></nav>")
    return "\n".join(rows)


def print_pdf(browser, html_path, pdf_path):
    profile = tempfile.mkdtemp(prefix="qhc_report_")
    try:
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-first-run", "--disable-extensions",
                        f"--user-data-dir={profile}", "--no-pdf-header-footer", "--virtual-time-budget=20000",
                        f"--print-to-pdf={pdf_path}", "file:///" + html_path.replace("\\", "/")],
                       check=True, capture_output=True, timeout=180)
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def heading_pages(pdf_path):
    """Page number of every named destination: Chrome writes one per link target, in a /Dests dictionary."""
    raw = open(pdf_path, "rb").read()

    def obj(n):
        return re.search(rb"\n%d 0 obj\s*(.*?)endobj" % n, raw, re.S).group(1)

    catalog = re.search(rb"/Type /Catalog(.*?)>>\s*endobj", raw, re.S).group(1)
    order = []

    def walk(n):
        node = obj(n)
        if re.search(rb"/Type\s*/Pages\b", node):
            for k in re.findall(rb"(\d+) 0 R", re.search(rb"/Kids\s*\[(.*?)\]", node, re.S).group(1)):
                walk(int(k))
        else:
            order.append(n)

    walk(int(re.search(rb"/Pages (\d+) 0 R", catalog).group(1)))
    page_of = {n: i + 1 for i, n in enumerate(order)}
    dests = obj(int(re.search(rb"/Dests (\d+) 0 R", catalog).group(1)))
    out = {}
    for name, ref in re.findall(rb"/([^\s/\[]+)\s*\[(\d+) 0 R", dests):
        key = re.sub(r"#([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), name.decode("latin-1"))
        out[key] = page_of[int(ref)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--browser")
    args = ap.parse_args()
    browser = find_browser(args.browser)
    html, heads = number(open(SRC, encoding="utf-8").read())
    try:
        with open(TMP, "w", encoding="utf-8") as f:
            f.write(html.replace("<!--TOC-->", toc(heads, {})))
        first = OUT + ".pass1.pdf"
        print_pdf(browser, TMP, first)
        pages = heading_pages(first)
        os.remove(first)
        missing = [hid for _, hid, _, _ in heads if hid not in pages]
        if missing:
            raise SystemExit(f"no page found for headings: {missing}")
        with open(TMP, "w", encoding="utf-8") as f:
            f.write(html.replace("<!--TOC-->", toc(heads, {k: str(v) for k, v in pages.items()})))
        print_pdf(browser, TMP, OUT)
        check = heading_pages(OUT)
        moved = [hid for _, hid, _, _ in heads if check.get(hid) != pages[hid]]
        if moved:
            raise SystemExit(f"pagination changed between passes for: {moved}")
    finally:
        if os.path.exists(TMP):
            os.remove(TMP)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({len(set(check.values()))} pages with headings, "
          f"last heading on page {max(check.values())})")


if __name__ == "__main__":
    main()
