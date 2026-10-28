# Research tool note: paperfetch

Applies only when the project settings list paperfetch under Research tools. It is an MCP server the human runs locally; its tool names, sources, and budgets belong to it and may change, so this note is what to update, not the phase guides. The phase guides only say: use the research tools listed in the settings, within budget, keep provenance, and report what you cannot get.

## What it does
Collects papers (metadata, abstracts, full text, open-access PDFs) into a local database and lets you search and read them without touching publisher pages. Sources include OpenAlex, Semantic Scholar, Europe PMC, Crossref, arXiv, PubMed, bioRxiv and medRxiv, and DBLP. Everything fetched once is cached.

## Cheap path first
1. `search_fulltext` and `list_papers` are local and free. Check what is already collected before searching the web.
2. `search_papers` with source `pubmed`, `dblp`, or `s2` is free. Source `openalex` is metered against a small daily budget; start with 25 to 50 results. `usage` shows what is left today.
3. `get_paper`, `add_papers`, `find_open_access`, `fill_abstracts`, `related_papers` are free or nearly free. Use `related_papers` to walk citations from one good paper instead of searching again.
4. `paper_outline` lists a paper's sections; `read_section` returns one section; `paper_tables` returns tables as rows. Read the methods or the data section, not the whole paper. `read_paper_text` fetches full text when you need it.
5. `annotate` and `collection` record what you learned, tagged, so the next session finds it with `search_fulltext`. `export_bibtex` turns a collection into a bibliography.

## Provenance
Record the paper key (`doi:...`, `arxiv:...`, `openalex:W...`) next to any fact, number, dataset, or baseline taken from it, in the brief, the data card, or the idea card.

## When it cannot get a paper
Some publishers block automated access even to open-access articles. When any result includes `manual_acquisition`, the tool is telling you the human must fetch it. Copy its message verbatim, with the paper title and the paper URL, into Requests for the human in `STATE.md` and into your session report. The required wording is:

> Acquire manually using the SCH Protocol: Automated Access Blocked

Do not retry it in a loop, do not claim to have read it, and do not drop it silently. Use the open-access alternatives you found meanwhile and say that you did. This is core invariant 8 applied to papers.
