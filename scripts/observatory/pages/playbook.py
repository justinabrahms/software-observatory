"""The playbook: /playbook/ and /playbook/<slug>/.

The index is three lists of triggers and nothing else: a reader should
recognise one line and click it. Each play page renders what the play's
frontmatter says, then what the build derives from doubts.yaml (what a
starting point already has closed, what a stack leaves untouched), then
the body. The derived parts are computed, not written, so a play cannot
claim more than the doubt graph grants it.
"""

import html

from ..dates import catalog_as_of
from ..jsonld import breadcrumb_ld, page_ld
from ..layout import html_page
from ..playbook import KIND_LABELS, KINDS, sort_key, stack_coverage
from ..taxonomy import FAMILIES, FAMILY_BY_SLUG

KIND_INTRO = {
    "symptom": ("What you noticed",
                "Something is wrong and you can say what it looks like. Each play "
                "names the doubt behind it, the sensor to point at it, and where "
                "to go if the doubt survives."),
    "starting-point": ("Where you are",
                       "What you already run decides what to add first. Each play "
                       "starts from a set of sensors and adds them in the order "
                       "that closes a new doubt at every step."),
    "composition": ("What you are building",
                    "A minimal stack for one shape of system, composed by distinct "
                    "doubts closed rather than one sensor per family."),
}


def _sensor_link(slug, by_slug):
    s = by_slug[slug]
    return f'<a href="/sensors/{slug}/" class="wikilink">{html.escape(s["title"])}</a>'


def _doubt_link(did, by_id):
    d = by_id[did]
    return (f'<a href="/what-each-sensor-proves/#{did}" class="wikilink">'
            f'{html.escape(d["name"].lower())}</a>')


def _doubt_list(ids, by_id):
    return ", ".join(_doubt_link(i, by_id) for i in ids)


def _edge_phrase(row, by_id):
    parts = []
    if row.get("closes"):
        parts.append("closes " + _doubt_list(row["closes"], by_id))
    if row.get("reveals"):
        parts.append("reveals " + _doubt_list(row["reveals"], by_id))
    return "; ".join(parts)


def _doubt_cell(row, by_id):
    """The doubt column of a stack table: closed doubts plain, revealed ones
    marked, since a retrospective row is a different promise."""
    parts = [_doubt_list(row["closes"], by_id)] if row.get("closes") else []
    if row.get("reveals"):
        parts.append("<em>reveals</em> " + _doubt_list(row["reveals"], by_id))
    return "; ".join(parts)


def _family_tag(slug, by_slug):
    fam = by_slug[slug].get("family", "")
    name = FAMILY_BY_SLUG.get(fam, {}).get("name", fam)
    return f'<span class="play-family" data-family="{html.escape(fam)}">{html.escape(name)}</span>'


# ── Per-kind sections ───────────────────────────────────────────────────────

def _symptom_sections(play, by_id, by_slug, by_play):
    d = by_id[play["doubt"]]
    misread = [s for s in d["misread_as_closing"] if s in by_slug]
    misread_html = ""
    if misread:
        misread_html = (
            '\n        <p class="play-doubt-misread">Commonly misread as closing it: '
            + ", ".join(_sensor_link(s, by_slug) for s in misread) + ".</p>")
    next_html = ""
    if play.get("next") and play["next"] in by_play:
        nxt = by_play[play["next"]]
        next_html = f"""
      <p class="play-next">Next play: <a href="/playbook/{nxt["slug"]}/" class="wikilink">{html.escape(nxt["title"])}</a></p>"""
    return f"""      <section class="play-noticed">
        <h2>You noticed</h2>
        <p>{html.escape(play["noticed"].strip())}</p>
      </section>
      <section class="play-doubt">
        <h2>The doubt</h2>
        <p><strong>{_doubt_link(d["id"], by_id)}.</strong> {html.escape(d["description"])}</p>{misread_html}
      </section>
      <div class="play-body signal-detail-body">
{play["body_html"]}
      </div>{next_html}"""


def _rows_html(rows, by_id, by_slug, ordered):
    tag = "ol" if ordered else "ul"
    items = []
    for row in rows:
        items.append(f"""          <li>
            <p class="play-row-head">{_sensor_link(row["sensor"], by_slug)} {_family_tag(row["sensor"], by_slug)}
              <span class="play-row-edge">{_edge_phrase(row, by_id)}</span></p>
            <p class="play-row-why">{html.escape(str(row["why"]).strip())}</p>
          </li>""")
    return f'        <{tag} class="play-rows">\n' + "\n".join(items) + f"\n        </{tag}>"


def _starting_point_sections(play, by_id, by_slug, doubts):
    have = [s for s in play.get("have") or [] if s in by_slug]
    closed, revealed, untouched = stack_coverage({"kind": "starting-point", "have": have, "steps": []}, doubts)
    n = len(doubts)
    have_html = ", ".join(_sensor_link(s, by_slug) for s in have) or "nothing"
    if closed:
        closed_sentence = (f"Already closed: {_doubt_list(closed, by_id)}. "
                           f"{len(closed)} of {n} doubts.")
    else:
        closed_sentence = f"Nothing on that list closes any of the {n} doubts."
    skip_html = ""
    if play.get("skip"):
        items = "\n".join(
            f"""          <li><p class="play-row-head">{_sensor_link(sk["sensor"], by_slug)}</p>
            <p class="play-row-why">{html.escape(str(sk["reason"]).strip())}</p></li>"""
            for sk in play["skip"] if sk.get("sensor") in by_slug)
        skip_html = f"""
      <section class="play-skip">
        <h2>What not to add yet</h2>
        <ul class="play-rows">
{items}
        </ul>
      </section>"""
    body_html = ""
    if play["body_html"].strip():
        body_html = f"""
      <div class="play-body signal-detail-body">
{play["body_html"]}
      </div>"""
    after_closed, after_revealed, after_untouched = stack_coverage(play, doubts)
    after = (f"After these steps: {len(after_closed)} of {n} doubts closed"
             + (f", {len(after_revealed)} more revealed after the fact" if after_revealed else "")
             + ". Still untouched: " + (_doubt_list(after_untouched, by_id) if after_untouched else "none") + ".")
    return f"""      <section class="play-where">
        <h2>Where you are</h2>
        <p>{html.escape(play["where"].strip())}</p>
        <p class="play-have">You run {have_html}. {closed_sentence}</p>
      </section>
      <section class="play-steps">
        <h2>Add in this order</h2>
        <p class="play-steps-lede">Each step closes a doubt the previous ones left open.</p>
{_rows_html(play["steps"], by_id, by_slug, ordered=True)}
        <p class="play-after">{after}</p>
      </section>{skip_html}{body_html}"""


def _composition_sections(play, by_id, by_slug, doubts):
    closed, revealed, untouched = stack_coverage(play, doubts)
    n = len(doubts)
    rows = "\n".join(
        f"""          <tr>
            <td>{_doubt_cell(row, by_id)}</td>
            <td>{_sensor_link(row["sensor"], by_slug)} {_family_tag(row["sensor"], by_slug)}</td>
            <td>{html.escape(str(row["why"]).strip())}</td>
          </tr>"""
        for row in play["stack"])
    left_open_html = ""
    if play.get("left_open"):
        items = "\n".join(
            f"""          <li><p class="play-row-head">{_doubt_link(lo["doubt"], by_id)}</p>
            <p class="play-row-why">{html.escape(str(lo["reason"]).strip())}</p></li>"""
            for lo in play["left_open"] if lo.get("doubt") in by_id)
        left_open_html = f"""
      <section class="play-left-open">
        <h2>Left open, on purpose</h2>
        <ul class="play-rows">
{items}
        </ul>
      </section>"""
    body_html = ""
    if play["body_html"].strip():
        body_html = f"""
      <div class="play-body signal-detail-body">
{play["body_html"]}
      </div>"""
    counted = (f"{len(play['stack'])} sensors close {len(closed)} of {n} doubts"
               + (f" and reveal {len(revealed)} more after the fact" if revealed else "") + ".")
    if untouched:
        mistaken = (f"{counted} It says nothing about {_doubt_list(untouched, by_id)}. "
                    "A green board from this stack is not evidence against any of those.")
    else:
        mistaken = f"{counted} Every doubt in the vocabulary is either closed, revealed, or deliberately left open above."
    return f"""      <section class="play-shape">
        <h2>The shape</h2>
        <p>{html.escape(play["shape"].strip())}</p>
      </section>
      <section class="play-stack">
        <h2>The stack</h2>
        <p class="play-steps-lede">One row per doubt. No two rows do the same job.</p>
        <div class="play-table-scroll">
        <table class="play-table">
          <thead><tr><th scope="col">Doubt</th><th scope="col">Sensor</th><th scope="col">Why this one</th></tr></thead>
          <tbody>
{rows}
          </tbody>
        </table>
        </div>
      </section>{left_open_html}
      <section class="play-mistaken">
        <h2>What this stack is mistaken for proving</h2>
        <p>{mistaken}</p>
      </section>{body_html}"""


# ── The stack check ─────────────────────────────────────────────────────────

def _stack_check_html(doubts, sensors):
    """The "what do you already run?" checklist at the top of the index.

    Every checkbox carries the doubts its sensor closes and reveals, straight
    from doubts.yaml, and a hidden list carries the doubt names; js/main.js
    only ticks, counts, and picks the addition that closes the most of what
    is left. Nothing about the graph lives in the script, so the checklist
    cannot disagree with the plays or the doubts page. Without JavaScript
    it is a checklist of the catalog by family, which is still a page."""
    by_family = {}
    for s in sensors:
        by_family.setdefault(s.get("family", ""), []).append(s)
    closes_of = {s["slug"]: [] for s in sensors}
    reveals_of = {s["slug"]: [] for s in sensors}
    for d in doubts:
        for slug in d["closed_by"]:
            if slug in closes_of:
                closes_of[slug].append(d["id"])
        for slug in d["revealed_by"]:
            if slug in reveals_of:
                reveals_of[slug].append(d["id"])

    groups = []
    for fam in FAMILIES:
        members = sorted(by_family.get(fam["slug"], []), key=lambda s: s["title"])
        if not members:
            continue
        boxes = "\n".join(
            f'          <label class="stack-box{"" if closes_of[s["slug"]] or reveals_of[s["slug"]] else " stack-box--silent"}">'
            f'<input type="checkbox" name="sensor" value="{s["slug"]}" '
            f'data-closes="{" ".join(closes_of[s["slug"]])}" '
            f'data-reveals="{" ".join(reveals_of[s["slug"]])}"> '
            f'{html.escape(s["title"])}</label>'
            for s in members)
        groups.append(f"""        <fieldset class="stack-family" data-family="{fam["slug"]}">
          <legend>{html.escape(fam["name"])}</legend>
{boxes}
        </fieldset>""")

    doubt_items = "\n".join(
        f'        <li data-d="{d["id"]}" data-closable="{1 if d["closed_by"] else 0}">'
        f'{html.escape(d["name"])}</li>'
        for d in doubts)
    n = len(doubts)
    return f"""    <section class="stack-check" id="your-stack">
      <h2>What do you already run?</h2>
      <p class="play-group-lede">
        Tick the sensors you run. The page says which of the {n} doubts they
        close, which are still open, and which one addition would close the
        most of what is left. Two sensors that close the same doubt count
        once; a sensor with no doubt edge in the vocabulary counts for
        nothing here, however useful it is.
      </p>
      <form class="stack-form" autocomplete="off">
{chr(10).join(groups)}
        <p class="stack-actions"><button type="reset" class="stack-clear">Clear</button>
          <span class="stack-tally"></span>
          <span class="stack-remember">Your ticks stay in this browser.</span></p>
      </form>
      <div class="stack-result" id="stack-result" hidden aria-live="polite"></div>
      <ul class="stack-doubts" hidden>
{doubt_items}
      </ul>
      <noscript><p class="stack-noscript">The count needs JavaScript. The
        <a href="/what-each-sensor-proves/#by-sensor" class="wikilink">by-sensor table</a>
        on the doubts page has the same edges as a static list.</p></noscript>
    </section>
"""


# ── Pages ───────────────────────────────────────────────────────────────────

def play_description(play, by_id):
    if play["kind"] == "symptom":
        return " ".join(play["noticed"].split())
    if play["kind"] == "starting-point":
        return " ".join(play["where"].split())
    return " ".join(play["shape"].split())


def generate_play_page(play, plays, doubts, sensors, output_dir):
    by_id = {d["id"]: d for d in doubts}
    by_slug = {s["slug"]: s for s in sensors}
    by_play = {p["slug"]: p for p in plays}
    kind = play["kind"]
    if kind == "symptom":
        sections = _symptom_sections(play, by_id, by_slug, by_play)
    elif kind == "starting-point":
        sections = _starting_point_sections(play, by_id, by_slug, doubts)
    else:
        sections = _composition_sections(play, by_id, by_slug, doubts)

    trail = [("Playbook", "/playbook/"), (play["title"], None)]
    crumbs = " › ".join(
        f'<a href="{path}">{html.escape(name)}</a>' if path else html.escape(name)
        for name, path in trail)
    body = f"""  <div class="play-layout">
    <article class="play">
      <p class="breadcrumb">{crumbs}</p>
      <header class="page-header page-header--play">
        <p class="eyebrow">{html.escape(KIND_LABELS[kind])}</p>
        <h1 class="page-title">{html.escape(play["title"])}</h1>
      </header>
{sections}
      <p class="play-back"><a href="/playbook/" class="wikilink">All plays</a></p>
    </article>
  </div>"""
    description = play_description(play, by_id)
    path = f"/playbook/{play['slug']}/"
    page_html = html_page(
        play["title"], body, canonical=path.lstrip("/"),
        description=description,
        json_ld=[
            page_ld("WebPage", play["title"], path, description,
                    extra={"dateModified": catalog_as_of(sensors)}),
            breadcrumb_ld(trail),
        ],
    )
    out_path = output_dir / "playbook" / play["slug"] / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_playbook_index(plays, doubts, sensors, output_dir):
    by_id = {d["id"]: d for d in doubts}
    by_slug = {s["slug"]: s for s in sensors}
    ordered = sorted(plays, key=sort_key)
    groups = []
    for kind in KINDS:
        members = [p for p in ordered if p["kind"] == kind]
        if not members:
            continue
        heading, lede = KIND_INTRO[kind]
        items = []
        for p in members:
            if kind == "symptom":
                sub = "the doubt: " + html.escape(by_id[p["doubt"]]["name"].lower())
            elif kind == "starting-point":
                sub = f"{len(p['steps'])} steps"
            else:
                sub = f"{len(p['stack'])} sensors"
            items.append(
                f'          <li><a href="/playbook/{p["slug"]}/" class="play-link">'
                f'<span class="play-link-title">{html.escape(p["title"])}</span>'
                f'<span class="play-link-sub">{sub}</span></a></li>')
        groups.append(f"""    <section class="play-group play-group--{kind}">
      <h2>{html.escape(heading)}</h2>
      <p class="play-group-lede">{html.escape(lede)}</p>
      <ul class="play-list">
{chr(10).join(items)}
      </ul>
    </section>""")

    body = f"""  <section class="page-header page-header--reading">
    <p class="eyebrow">The Playbook</p>
    <h1 class="page-title">The playbook</h1>
    <p class="page-lede">
      Start from what you already run, what you noticed, where you are, or
      what you are building. Each play names the doubt, the sensor to point
      at it, and where to go next. The catalog is the reference; this is the
      route through it.
    </p>
  </section>

  <div class="playbook-content">
{_stack_check_html(doubts, sensors)}
{chr(10).join(groups)}
  </div>"""
    description = ("Situational plays for the sensor catalog: what to point at a "
                   "symptom, what to add first from where you are, and a minimal "
                   "stack for each shape of system.")
    title = "The Playbook"
    page_html = html_page(
        title, body, canonical="playbook/", description=description,
        json_ld=[
            page_ld("CollectionPage", title, "/playbook/", description,
                    extra={"dateModified": catalog_as_of(sensors)}),
            breadcrumb_ld([("Playbook", None)]),
        ],
    )
    out_path = output_dir / "playbook" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)


def generate_playbook(plays, doubts, sensors, output_dir):
    generate_playbook_index(plays, doubts, sensors, output_dir)
    for play in plays:
        generate_play_page(play, plays, doubts, sensors, output_dir)
