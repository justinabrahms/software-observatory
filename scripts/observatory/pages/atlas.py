"""The atlas: /atlas/."""

import html

from ..layout import html_page
from ..jsonld import breadcrumb_ld, page_ld
from ..taxonomy import (
    FAMILIES,
    FAMILY_BY_SLUG,
    LIFECYCLE_STAGES,
    STAGE_BY_LEVEL,
    family_url,
)


def generate_atlas_page(sensors, output_dir):
    """Generate the atlas page: a family x lifecycle-stage grid, plus a
    dependency map of how families lean on each other."""

    # Group sensors by family
    by_family = {}
    for s in sensors:
        fam = s.get("family", "uncategorized")
        by_family.setdefault(fam, []).append(s)

    # Grid: rows = families, columns = lifecycle stages
    matrix_rows = ""
    for family in FAMILIES:
        fam_sensors = by_family.get(family["slug"], [])

        matrix_rows += f"""        <div class="matrix-row">
          <div class="matrix-row-label">
            <span class="matrix-fam-num">{family['num']}</span>
            <span class="matrix-fam-icon fam-{family['slug']}" aria-hidden="true">{family['icon']}</span>
            <a href="{family_url(family["slug"])}" class="matrix-fam-name">{html.escape(family['name'])}</a>
          </div>
"""

        for stage in LIFECYCLE_STAGES:
            cell_sensors = []
            for s in fam_sensors:
                stage_slug = STAGE_BY_LEVEL.get(s.get("stack_level", ""), "")
                if stage_slug == stage["slug"]:
                    cell_sensors.append(s)

            if cell_sensors:
                chips = ""
                for s in cell_sensors:
                    chips += f'<a href="/sensors/{s["slug"]}/" class="matrix-chip">{html.escape(s["title"])}</a>\n'
                matrix_rows += f"""          <div class="matrix-cell has-sensors">
            {chips.rstrip()}
          </div>
"""
            else:
                matrix_rows += '          <div class="matrix-cell empty"></div>\n'

        matrix_rows += "        </div>\n"

    # Column headers (earliest signal first)
    col_headers = ""
    for stage in LIFECYCLE_STAGES:
        col_headers += f"""            <div class="matrix-col-header" title="{html.escape(stage['desc'])}">
              <span class="col-label">{html.escape(stage['label'])}</span>
            </div>
"""

    # Family dependency graph, drawn from see_also references.
    # A reference from a sensor in family A to family B means A leans on B.
    fam_slug_aliases = {}
    for f in FAMILIES:
        fam_slug_aliases[f["slug"]] = f["slug"]
        fam_slug_aliases[f["slug"] + "-family"] = f["slug"]

    sensors_by_id = {s["id"]: s for s in sensors}
    # edge key: (src, tgt); value: list of contributing sensor titles
    edge_sensors = {}
    for s in sensors:
        src = s.get("family", "")
        if not src:
            continue
        for ref in s.get("see_also", []):
            tgt = None
            if ref in fam_slug_aliases:
                tgt = fam_slug_aliases[ref]
            elif ref in sensors_by_id:
                tgt = sensors_by_id[ref].get("family", "")
            if tgt and tgt != src:
                key = (src, tgt)
                edge_sensors.setdefault(key, [])
                if s["title"] not in edge_sensors[key]:
                    edge_sensors[key].append(s["title"])

    # Keep the strongest edges (most contributing sensors), one direction per pair
    pair_best = {}
    for (src, tgt), titles in edge_sensors.items():
        pair = tuple(sorted([src, tgt]))
        if pair not in pair_best or len(titles) > len(pair_best[pair][2]):
            pair_best[pair] = (src, tgt, titles)

    strong_edges = sorted(pair_best.values(), key=lambda e: -len(e[2]))[:14]

    # Compact label for each edge: use the shortest contributing sensor title
    def short_label(titles):
        return min(titles, key=len) if titles else ""

    # Layout: place nodes on a circle
    import math
    n = len(FAMILIES)
    cx, cy, radius = 560, 460, 340
    node_pos = {}
    for i, f in enumerate(FAMILIES):
        angle = (2 * math.pi * i / n) - math.pi / 2
        node_pos[f["slug"]] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))

    NODE_R = 9

    def edge_geometry(p1, p2, bend=0.18):
        """Trim the line to start/end at the circle rims, return (path_d, tip, tip_angle)."""
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        norm = math.hypot(dx, dy) or 1
        ux, uy = dx / norm, dy / norm
        s = (p1[0] + ux * NODE_R, p1[1] + uy * NODE_R)
        e = (p2[0] - ux * NODE_R, p2[1] - uy * NODE_R)
        mx, my = (s[0] + e[0]) / 2, (s[1] + e[1]) / 2
        edx, edy = e[0] - s[0], e[1] - s[1]
        qx, qy = mx - edy * bend, my + edx * bend
        path_d = f"M {s[0]:.1f} {s[1]:.1f} Q {qx:.1f} {qy:.1f} {e[0]:.1f} {e[1]:.1f}"
        # Tangent at the end of a quadratic bezier: (e - q)
        tip_angle = math.atan2(e[1] - qy, e[0] - qx)
        return path_d, e, tip_angle

    def arrowhead_points(tip, angle, size=8):
        """Triangle pointing along `angle` with apex at `tip`."""
        ax, ay = tip
        perp = angle + math.pi / 2
        b1x = ax - size * math.cos(angle) + (size * 0.5) * math.cos(perp)
        b1y = ay - size * math.sin(angle) + (size * 0.5) * math.sin(perp)
        b2x = ax - size * math.cos(angle) - (size * 0.5) * math.cos(perp)
        b2y = ay - size * math.sin(angle) - (size * 0.5) * math.sin(perp)
        return f"{ax:.1f},{ay:.1f} {b1x:.1f},{b1y:.1f} {b2x:.1f},{b2y:.1f}"

    def edge_label_pos(p1, p2, bend=0.18, t=0.5):
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        qx, qy = mx - dy * bend, my + dx * bend
        x = (1 - t) ** 2 * p1[0] + 2 * (1 - t) * t * qx + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p1[1] + 2 * (1 - t) * t * qy + t ** 2 * p2[1]
        # Nudge perpendicular to the curve so the label floats off the stroke
        norm = math.hypot(dx, dy) or 1
        off = 12
        x += (-dy / norm) * off
        y += (dx / norm) * off
        return x, y

    edges_svg = ""
    labels_svg = ""
    for idx, (src, tgt, titles) in enumerate(strong_edges):
        p1, p2 = node_pos[src], node_pos[tgt]
        # Vary bend direction slightly per edge to reduce overlap
        bend = 0.18 if idx % 2 == 0 else -0.18
        path_d, tip, tip_angle = edge_geometry(p1, p2, bend)
        lx, ly = edge_label_pos(p1, p2, bend)
        why = short_label(titles)
        cls = "dep-edge"
        tip_pts = arrowhead_points(tip, tip_angle)
        edges_svg += f'          <path class="{cls}" data-src="{src}" data-tgt="{tgt}" d="{path_d}"><title>{html.escape(src)} leans on {html.escape(tgt)}</title></path>\n'
        edges_svg += f'          <polygon class="dep-arrowhead" data-src="{src}" data-tgt="{tgt}" points="{tip_pts}" />\n'
        labels_svg += f'          <text class="dep-edge-label" data-src="{src}" data-tgt="{tgt}" x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle"><title>{html.escape(", ".join(titles))}</title>{html.escape(why)}</text>\n'

    nodes_svg = ""
    for f in FAMILIES:
        x, y = node_pos[f["slug"]]
        # Push label anchor outward based on position relative to center
        anchor = "start" if x > cx + 10 else ("end" if x < cx - 10 else "middle")
        lx = x + (16 if anchor == "start" else (-16 if anchor == "end" else 0))
        ly = y + (-18 if y < cy - 10 else (28 if y > cy + 10 else 4))
        nodes_svg += f"""          <a href="{family_url(f["slug"])}" class="dep-node" data-family="{f['slug']}">
            <circle cx="{x:.1f}" cy="{y:.1f}" r="9" class="dep-node-dot" />
            <text class="dep-node-label" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}">{html.escape(f['name'])}</text>
          </a>
"""

    dep_graph_svg = f"""      <svg class="dep-graph" viewBox="0 0 1120 920" role="img" aria-label="Family dependency graph: how sensor families lean on each other">
        <title>Family dependency graph</title>
        <desc>Arrows point from the family that leans to the family it leans on. {len(edge_sensors)} edges shown. See the text list below the graph for the full edge set.</desc>
{edges_svg.rstrip()}
{labels_svg.rstrip()}
{nodes_svg.rstrip()}
      </svg>"""

    # Text equivalent of the dependency graph for screen readers
    edge_list = ""
    for (src, tgt), sensor_titles in sorted(edge_sensors.items()):
        src_name = FAMILY_BY_SLUG.get(src, {}).get("name", src)
        tgt_name = FAMILY_BY_SLUG.get(tgt, {}).get("name", tgt)
        edge_list += f'        <li>{html.escape(src_name)} leans on {html.escape(tgt_name)} via: {html.escape(", ".join(sorted(sensor_titles)))}</li>\n'
    edge_list_html = f"""      <details class="sr-only">
        <summary>Family dependency graph (text)</summary>
        <ul>
{edge_list.rstrip()}
        </ul>
      </details>"""

    # Family map
    family_map = ""
    for f in FAMILIES:
        family_map += f"""        <a href="{family_url(f["slug"])}" class="family-map-card">
          <span class="fam-num">{f['num']}</span>
          <span class="fam-name">{html.escape(f['name'])}</span>
          <span class="fam-q">"{html.escape(f['question'])}"</span>
        </a>
"""

    body = f"""  <div class="atlas-container">
    <section class="page-header">
      <p class="eyebrow">The Atlas</p>
      <h1 class="page-title">Sensor Atlas</h1>
      <p class="page-lede">
        A navigational map of the sensor landscape. Each row is a
        <a href="/catalog/" class="wikilink">sensor family</a> — a question
        you're asking about the system. Each column is a stage of the software
        lifecycle — <em>when</em> the signal becomes available, from authoring
        the code on the left to observing real-world outcomes on the right.
        For the narrative version of how evidence accumulates, see the
        <a href="/#confidence-stack" class="wikilink">confidence stack</a>.
      </p>
    </section>

    <div class="atlas-intro">
      <p style="color:var(--text-soft);max-width:44rem;line-height:1.7;">
        Use the atlas to orient yourself. <em>What question are you
        asking?</em> Find the row. <em>When can you afford to learn the
        answer?</em> Find the column. Empty cells are questions nobody
        instrumented at that stage yet.
      </p>
    </div>

    <!-- Grid -->
    <div class="atlas-matrix-wrapper">
      <div class="atlas-matrix">
        <div class="matrix-header-row">
          <div class="matrix-corner"></div>
{col_headers.rstrip()}
        </div>
{matrix_rows.rstrip()}
      </div>
    </div>

    <!-- Axis labels -->
    <div class="atlas-axes">
      <div class="axis-label-h">← What question are you asking? (sensor families)</div>
      <div class="axis-label-v">← earlier / cheaper &nbsp;&nbsp;|&nbsp;&nbsp; later / closer to reality → <br>Lifecycle stages</div>
    </div>

    <!-- Family map -->
    <div class="family-map-section">
      <h2 class="section-heading">{len(FAMILIES)} families at a glance</h2>
      <div class="family-map-grid">
{family_map.rstrip()}
      </div>
    </div>

    <!-- Dependency graph -->
    <div class="dep-map-section">
      <h2 class="section-heading">How the families lean on each other</h2>
      <p class="dep-map-lede">
        Sensor families are not a stack — evidence from one family routinely
        depends on another family having done its job. Arrows point from the
        family that leans to the family it leans on, labelled with a sensor
        that carries the connection. Hover a node to isolate its
        neighborhood. Drawn from the cross-references inside the catalog
        entries themselves; only the strongest links are shown.
      </p>
      <div class="dep-graph-wrapper">
{dep_graph_svg}
      </div>
{edge_list_html}
    </div>
  </div>"""

    description = (
        f"A map of the {len(FAMILIES)} sensor families against the "
        "software lifecycle: which signals are available while you write "
        "code, and which only appear in production."
    )
    page_html = html_page(
        "Sensor Atlas", body, canonical="atlas/",
        description=description,
        json_ld=[
            page_ld("CollectionPage", "Sensor Atlas", "/atlas/", description),
            breadcrumb_ld([("Atlas", None)]),
        ],
    )
    out_path = output_dir / "atlas" / "index.html"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(page_html)
