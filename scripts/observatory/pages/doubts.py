"""The doubts page: /what-each-sensor-proves/.

A three-column graph drawn from content/doubts.yaml. Sensors run down both
sides in family order; the doubts sit between them. A sensor on the left is
one whose green reading is misread as closing the doubt. A sensor on the
right closes the doubt before shipping, or reveals it after the fact.

The SVG is rendered here, not in the browser, so the page carries its
content without JavaScript; js/main.js only adds the hover-and-click
isolation. The per-doubt list under the figure is the same data as prose,
which is what a reader without a pointer, or a crawler, gets.
"""

import html

from ..dates import catalog_as_of
from ..doubts import families_of, origin_counts, prose_claims
from ..jsonld import breadcrumb_ld, page_ld
from ..layout import html_page
from ..taxonomy import FAMILIES

WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
         "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
         "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]


def number_word(n):
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)

# Layout, in SVG user units. Chosen for the content: 59 rows of 19px with a
# family heading every few rows, and a doubt box wide enough for the longest
# name in one line.
ROW = 19
HEAD = 30
GAP = 12
WIDTH = 1200
LEFT_TEXT = 262     # left column labels end here (right-aligned)
LEFT_DOT = 276
MID = 600           # doubt box centre
MID_HALF = 110      # half the box width
BOX_H = 40
RIGHT_DOT = 924
RIGHT_TEXT = 938    # right column labels start here

EDGE_KINDS = (
    ("misread_as_closing", "misread"),
    ("closed_by", "closes"),
    ("revealed_by", "reveals"),
)


def _curve(x1, y1, x2, y2):
    cx = (x1 + x2) / 2
    return f"M{x1},{y1:.1f} C{cx},{y1:.1f} {cx},{y2:.1f} {x2},{y2:.1f}"


def _layout(doubts, sensors):
    """Row positions for every sensor (both columns share them) and a y for
    every doubt. Returns (rows, heads, doubt_y, connected_bottom, height)."""
    by_slug = {s["slug"]: s for s in sensors}
    edges = []
    for d in doubts:
        for key, kind in EDGE_KINDS:
            for slug in d[key]:
                edges.append((d["id"], slug, kind))
    degree = {}
    for _, slug, _ in edges:
        degree[slug] = degree.get(slug, 0) + 1

    y = 48
    rows = []       # (slug, y, orphan)
    heads = []      # (label, y)
    for fam in FAMILIES:
        members = sorted(
            (s for s in sensors if s.get("family") == fam["slug"] and degree.get(s["slug"])),
            key=lambda s: s["title"])
        if not members:
            continue
        heads.append((fam["name"], y))
        y += HEAD
        for s in members:
            rows.append((s["slug"], y, False))
            y += ROW
        y += GAP
    connected_bottom = y
    orphans = sorted((s for s in sensors if not degree.get(s["slug"])), key=lambda s: s["title"])
    y += 6
    orphan_head_y = y
    y += HEAD
    for s in orphans:
        rows.append((s["slug"], y, True))
        y += ROW
    height = y + 16
    y_of = {slug: yy for slug, yy, _ in rows}

    # Doubts are ordered by the mean height of the sensors they touch, then
    # spread evenly over the connected span so the boxes never overlap.
    def mean_y(d):
        ys = [y_of[s] for key, _ in EDGE_KINDS for s in d[key]]
        return sum(ys) / len(ys) if ys else connected_bottom / 2
    ordered = sorted(doubts, key=mean_y)
    span_top = 48 + BOX_H
    span_bottom = connected_bottom - BOX_H
    step = (span_bottom - span_top) / max(len(ordered) - 1, 1)
    doubt_y = {d["id"]: span_top + i * step for i, d in enumerate(ordered)}
    return rows, heads, orphan_head_y, doubt_y, edges, degree, connected_bottom, height, by_slug


def render_graph_svg(doubts, sensors):
    (rows, heads, orphan_head_y, doubt_y, edges, degree,
     connected_bottom, height, by_slug) = _layout(doubts, sensors)
    y_of = {slug: yy for slug, yy, _ in rows}
    misread_deg = {}
    closing_deg = {}
    for _, slug, kind in edges:
        target = misread_deg if kind == "misread" else closing_deg
        target[slug] = target.get(slug, 0) + 1

    out = [f'<svg class="doubt-graph" viewBox="0 0 {WIDTH} {height}" role="img" '
           'aria-label="Three-column graph: sensors misread as closing each doubt '
           'on the left, the doubts in the middle, sensors that close or reveal '
           'each doubt on the right.">']
    out.append("<g>")
    for did, slug, kind in edges:
        ys, yd = y_of[slug], doubt_y[did]
        if kind == "misread":
            d = _curve(LEFT_DOT + 6, ys, MID - MID_HALF, yd)
        else:
            d = _curve(MID + MID_HALF, yd, RIGHT_DOT - 6, ys)
        out.append(f'<path class="edge {kind}" d="{d}" data-s="{slug}" data-d="{did}"/>')
    out.append("</g>")

    out.append("<g>")
    out.append(f'<text class="col-head misread" x="{LEFT_TEXT}" y="22" text-anchor="end">Misread as closing it</text>')
    out.append(f'<text class="col-head" x="{MID}" y="22" text-anchor="middle">Doubt</text>')
    out.append(f'<text class="col-head closes" x="{RIGHT_TEXT}" y="22">Closes it, or reveals it after</text>')
    for label, yy in heads:
        out.append(f'<text class="fam-head" x="{LEFT_TEXT}" y="{yy + 14}" text-anchor="end">{html.escape(label)}</text>')
        out.append(f'<text class="fam-head" x="{RIGHT_TEXT}" y="{yy + 14}">{html.escape(label)}</text>')
    if any(orphan for _, _, orphan in rows):
        out.append(f'<line class="rule" x1="40" y1="{connected_bottom}" x2="{LEFT_TEXT + 30}" y2="{connected_bottom}"/>')
        out.append(f'<line class="rule" x1="{RIGHT_TEXT - 30}" y1="{connected_bottom}" x2="{WIDTH - 40}" y2="{connected_bottom}"/>')
        out.append(f'<text class="fam-head" x="{LEFT_TEXT}" y="{orphan_head_y + 14}" text-anchor="end">No doubt edge</text>')
        out.append(f'<text class="fam-head" x="{RIGHT_TEXT}" y="{orphan_head_y + 14}">No doubt edge</text>')
    out.append("</g>")

    out.append("<g>")
    for slug, yy, orphan in rows:
        s = by_slug[slug]
        title = html.escape(s["title"])
        fam = html.escape(s.get("family", ""))
        cls_l = "sensor" + (" orphan" if orphan else "") + ("" if misread_deg.get(slug) else " idle")
        cls_r = "sensor" + (" orphan" if orphan else "") + ("" if closing_deg.get(slug) else " idle")
        out.append(f'<g class="{cls_l}" data-s="{slug}" data-side="l">'
                   f'<text class="s-label" x="{LEFT_TEXT}" y="{yy + 4}" text-anchor="end">{title}</text>'
                   f'<circle class="s-dot" cx="{LEFT_DOT}" cy="{yy}" r="4" fill="var(--fam-{fam})"/></g>')
        out.append(f'<g class="{cls_r}" data-s="{slug}" data-side="r">'
                   f'<circle class="s-dot" cx="{RIGHT_DOT}" cy="{yy}" r="4" fill="var(--fam-{fam})"/>'
                   f'<text class="s-label" x="{RIGHT_TEXT}" y="{yy + 4}">{title}</text></g>')
    out.append("</g>")

    out.append("<g>")
    for d in doubts:
        yy = doubt_y[d["id"]]
        sub = f'{len(d["misread_as_closing"])} misread · {len(d["closed_by"])} close'
        if d["revealed_by"]:
            sub += f' · {len(d["revealed_by"])} reveal'
        out.append(f'<g class="doubt" data-d="{d["id"]}">'
                   f'<rect class="d-node" x="{MID - MID_HALF}" y="{yy - BOX_H / 2:.1f}" width="{MID_HALF * 2}" height="{BOX_H}" rx="3"/>'
                   f'<text class="d-name" x="{MID}" y="{yy - 1:.1f}" text-anchor="middle">{html.escape(d["name"])}</text>'
                   f'<text class="d-sub" x="{MID}" y="{yy + 14:.1f}" text-anchor="middle">{sub}</text></g>')
    out.append("</g>")
    out.append("</svg>")
    return "\n".join(out)


def render_by_sensor_table(doubts, sensors):
    """One row per sensor in family order; the cells hold the doubts it is
    misread as closing, closes, and reveals, each linked to its definition.
    A sensor with no edge keeps its row, muted, so a reader looking for it
    finds it and sees that the vocabulary has nothing for it yet."""
    per_sensor = {s["slug"]: {k: [] for k, _ in EDGE_KINDS} for s in sensors}
    for d in doubts:
        for key, _ in EDGE_KINDS:
            for slug in d[key]:
                per_sensor[slug][key].append(d)

    def cell(ds):
        if not ds:
            return '<td class="empty"></td>'
        return "<td>" + "".join(
            f'<a href="#{d["id"]}" class="doubt-ref">{html.escape(d["name"])}</a>' for d in ds) + "</td>"

    rows = []
    for fam in FAMILIES:
        members = sorted((s for s in sensors if s.get("family") == fam["slug"]), key=lambda s: s["title"])
        if not members:
            continue
        rows.append(f'<tr class="fam-row"><th scope="rowgroup" colspan="4">{html.escape(fam["name"])}</th></tr>')
        for s in members:
            e = per_sensor[s["slug"]]
            idle = not any(e.values())
            rows.append(
                f'<tr{" class=\"idle\"" if idle else ""}>'
                f'<th scope="row"><a href="/sensors/{s["slug"]}/" class="wikilink">{html.escape(s["title"])}</a></th>'
                + cell(e["misread_as_closing"]) + cell(e["closed_by"]) + cell(e["revealed_by"]) + "</tr>")
    return (
        '<table class="doubt-table">\n<thead><tr><th scope="col">Sensor</th>'
        '<th scope="col" class="misread">Misread as closing</th>'
        '<th scope="col" class="closes">Closes</th>'
        '<th scope="col" class="reveals">Reveals after</th></tr></thead>\n<tbody>\n'
        + "\n".join(rows) + "\n</tbody>\n</table>")


def generate_doubts_page(doubts, sensors, output_dir):
    by_slug = {s["slug"]: s for s in sensors}
    n_sensors = len(sensors)

    chips = "\n".join(
        f'      <button type="button" class="doubt-chip" data-d="{d["id"]}">'
        f'<span class="name">{html.escape(d["name"])}</span>'
        f'<span class="counts"><span class="m"><b>{len(d["misread_as_closing"])}</b> misread</span>'
        f'<span class="c"><b>{len(d["closed_by"])}</b> close</span>'
        + (f'<span class="r"><b>{len(d["revealed_by"])}</b> reveal</span>' if d["revealed_by"] else "")
        + "</span></button>"
        for d in doubts)

    entries = "\n".join(
        f'''    <div class="doubt-def" id="{d["id"]}">
      <dt class="doubt-def-name">{html.escape(d["name"])}</dt>
      <dd class="doubt-def-desc">{html.escape(d["description"])}</dd>
    </div>'''
        for d in doubts)

    claims = {c.label: c for c in prose_claims(doubts, sensors)}

    def claim_sentence(label):
        c = claims[label]
        # A claim that applies and fails has already failed the build in
        # validate_doubts; here it can only apply-and-hold or not apply.
        return c.sentence if c.applies and c.holds else ""

    by_id = {d["id"]: d for d in doubts}
    wrong_spec_sentence = ""
    ws = by_id.get("wrong-specification")
    if ws is not None:
        n_close = len(families_of(ws["closed_by"], by_slug))
        n_misread = len(families_of(ws["misread_as_closing"], by_slug))
        wrong_spec_sentence = (
            f"<em>Wrong specification</em> draws its closers from "
            f"{number_word(n_close)} famil{'y' if n_close == 1 else 'ies'} and its "
            f"misreadings from {number_word(n_misread)}. ")

    future_ids = ["structure-decayed", "risk-concentrated", "unexplained"]
    future_sentence = ""
    if all(i in by_id for i in future_ids):
        names = [f'<a href="#{i}">{html.escape(by_id[i]["name"].lower())}</a>' for i in future_ids]
        future_sentence = (
            f"Three doubts, {names[0]}, {names[1]} and {names[2]}, are about "
            "the codebase's future rather than its correctness, and they are "
            "what the evolution and comprehension families exist for.")

    origins = origin_counts(doubts)
    origin_sentence = (
        f"{number_word(origins['mined']).capitalize()} of the doubts "
        f"{'was' if origins['mined'] == 1 else 'were'} mined "
        'from the "What it cannot detect" section of every entry, which is '
        "where the catalog names what it leaves open.")
    coverage_sentence = (
        f"The other {number_word(origins['coverage'])} came from asking every "
        "sensor the first pass left with nothing to close what it does close.")

    body = f"""  <section class="page-header page-header--reading">
    <p class="eyebrow">The Framework</p>
    <h1 class="page-title">What each sensor proves</h1>
    <p class="page-lede">
      What does a passing type check, a green test suite, or 90% coverage
      actually prove about the code, and what is it mistaken for proving?
      The <a href="/framework/#combining-sensors" class="wikilink">composition
      rule</a> asks of every sensor: what doubt does this eliminate that the
      others leave open? This page is the answer for the whole catalog.
      {len(doubts)} doubts about a system, and for each one the sensors that
      close it, the sensors that only reveal it after the fact, and the
      sensors whose green reading is mistaken for closing it.
    </p>
  </section>

  <div class="framework-content doubts-content">
    <div class="doubt-intro">
      <p>
        No sensor in the catalog measures correctness. Each one answers a
        narrower question, and the
        <a href="/framework/#combining-sensors" class="wikilink">composition
        rule</a> says how those answers add up: not by counting green checks,
        but by ruling out specific ways the software could be wrong, one at a
        time. A check that rules out nothing new adds nothing, however green
        it is. This page names those ways of being wrong and maps every
        sensor onto them.
      </p>
      <p>
        A <em>doubt</em> is one specific way the software could be wrong. The
        logic is wrong even though it compiles. The tests ran the code but
        asserted nothing about the result. The change altered something
        nobody meant to touch. There are {len(doubts)} here, and for each one
        the page asks three questions of every sensor. Does a clean result
        from this sensor <strong>close</strong> the doubt, for what the sensor
        was pointed at? Does it only <strong>reveal</strong> the doubt after
        the fact, once the damage has reached production? Or is its clean
        result commonly <strong>misread</strong> as closing the doubt when it
        does not?
      </p>
      <p>
        The graph below draws all three answers at once, with the doubts in
        the middle and the sensors on either side. Hover or click anything to
        isolate it. Under the graph the same data is laid out by sensor, for
        when you arrive with a tool in mind and want to know what it proves,
        and each doubt is defined at the end.
      </p>
    </div>

    <div class="doubt-legend">
      <span><svg viewBox="0 0 34 10" aria-hidden="true"><line x1="1" y1="5" x2="33" y2="5" class="lg-misread"/></svg>green is misread as closing this doubt</span>
      <span><svg viewBox="0 0 34 10" aria-hidden="true"><line x1="1" y1="5" x2="33" y2="5" class="lg-closes"/></svg>closes the doubt before shipping</span>
      <span><svg viewBox="0 0 34 10" aria-hidden="true"><line x1="1" y1="5" x2="33" y2="5" class="lg-reveals"/></svg>reveals the doubt after the fact</span>
      <span>dot colour is the family; a sensor is lit on a side only where it has an edge there</span>
    </div>

    <div class="doubt-chips" role="group" aria-label="Doubts">
{chips}
    </div>
    <div class="doubt-detail" hidden></div>

    <figure class="doubt-figure">
      <div class="doubt-graph-scroll">
{render_graph_svg(doubts, sensors)}
      </div>
      <figcaption>
        The same {n_sensors} sensors appear on both sides, grouped by family in
        the catalog's order. A doubt sits at the average height of the sensors it
        touches. Hover or click a doubt or a sensor to isolate it. A doubt with
        an empty left side is one nothing gets mistaken for. The entries at the
        bottom have no edge in this vocabulary: some close a doubt it does not
        yet name, some are raw data that other sensors judge, and some are
        aggregates with nothing to attribute.
      </figcaption>
    </figure>

    <section class="doubt-by-sensor">
      <h2>By sensor</h2>
      <p class="doubt-by-sensor-lede">
        The same edges, one row per sensor. Each doubt links to its definition
        below.
      </p>
      <div class="doubt-table-scroll">
{render_by_sensor_table(doubts, sensors)}
      </div>
    </section>

    <section class="doubt-notes">
      <h2>Reading the edges</h2>
      <p>
        The misread edge is deliberately narrow. Every sensor that does not
        close a doubt leaves it open, which is nearly the whole catalog for any
        one doubt and not worth drawing. What the dashed edges mark is the
        specific mistake: 90% coverage taken as tested, a green canary taken as
        a safe release, "formally proven" taken as correct. That is the
        misreading each entry's "What it cannot detect" section was written to
        head off.
      </p>
      <p>
        No closing edge is unconditional. A proof covers its stated property,
        a test its stated examples, a canary the metrics it compares. That is
        the composition rule in one sentence, and it is why two sensors that
        close the same doubt count once.
      </p>
      <p>
        Retrospective sensors get their own edge. {claim_sentence("escaped-defect-rate reveals late-effects rather than closing it")}
        The catalog's <a href="/framework/#predictive-vs-retrospective" class="wikilink">predictive
        versus retrospective</a> dimension is the same distinction.
      </p>
      <h2>What the shape says</h2>
      <p>
        The vocabulary does not collapse into families. {claim_sentence("unasserted-execution's closers share one family with some of its misread sensors")}
        {wrong_spec_sentence}{future_sentence}
      </p>
      <p>
        {claim_sentence("missing-behavior and wrong-specification close only at review or user-outcome sensors")}
        {claim_sentence("wrong-logic has an empty misread side")}
      </p>
      <h2>Where the vocabulary came from</h2>
      <p>
        {origin_sentence} That method finds the catalog's residue, not its
        coverage: a doubt the catalog closes well never appears there, because
        no entry is worse at it than the sensor that owns it. {coverage_sentence}
      </p>
      <p>
        Every edge was then stated as a plain assertion, "most engineers think
        a passing X shows Y" or "X ensures Y", and judged true, partly true, or
        false by reviewers who saw only the assertion. The false ones were
        removed, and they were mostly misreadings: the reviewers' repeated
        finding was that engineers know what a compiler does not prove. No
        closing edge was judged fully true. The vocabulary lives in
        <code>content/doubts.yaml</code>, the build refuses a sensor it does
        not recognise, and every sentence above that names a specific doubt is
        checked against the file at build time.
      </p>
    </section>

    <section class="doubt-entries">
      <h2>The doubts, defined</h2>
      <dl class="doubt-defs">
{entries}
      </dl>
    </section>
  </div>"""

    description = (
        "What passing tests, type checks, coverage, canaries and proofs "
        f"actually prove about software: {len(doubts)} doubts, and for each "
        "the sensors that rule it out, the sensors that reveal it after the "
        "fact, and the sensors mistaken for ruling it out."
    )
    title = "What Each Sensor Proves, and What It Is Mistaken for Proving"
    page_html = html_page(
        title, body, canonical="what-each-sensor-proves/",
        description=description,
        json_ld=[
            page_ld("WebPage", title, "/what-each-sensor-proves/", description,
                    extra={"dateModified": catalog_as_of(sensors)}),
            breadcrumb_ld([("Framework", "framework/"),
                           ("What each sensor proves", None)]),
        ],
    )
    out_path = output_dir / "what-each-sensor-proves" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
