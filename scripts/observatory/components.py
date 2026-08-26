"""Small reusable HTML fragments — badges, dots, hover notes, the sensor card.

The pieces that appear on more than one page. Anything used by exactly one
generator stays in that generator; this module is the shared vocabulary of
markup, not a junk drawer."""

import html

from .render import blurb_text
from .taxonomy import INDEPENDENCE_DOTS, LATENCY_WORDS


def latency_badge_html(latency_key):
    """Small latency badge with full-word text and a hover tooltip."""
    word = LATENCY_WORDS[latency_key]
    tip = f"How long it takes to get this feedback: {word}"
    return (f'<span class="latency-badge" title="{html.escape(tip)}">'
            f'<span class="sr-only">Feedback latency: </span>~{html.escape(word)}</span>')


def note_hover_html(note):
    """A small (?) marker whose hover text carries extra color for a property."""
    if not note:
        return ""
    return (f' <span class="prop-note" title="{html.escape(note)}" '
            f'aria-label="{html.escape(note)}">(?)</span>')


def provisional_note_html(note):
    """A visible inline hedge rendered in the sidebar under the scalar it
    qualifies. Used for claims the field has not settled (e.g. model
    correlation effects on second-agent-review independence)."""
    if not note:
        return ""
    return ('\n          <dd class="provisional-note">Provisional — '
            f'{html.escape(note)}</dd>')


def oracle_dots_html(oracle_str):
    """Render the 5-dot oracle meter."""
    filled = {"maximum": 5, "high": 4, "medium": 3, "low": 2, "minimum": 1}.get(oracle_str, 0)
    dots = ""
    for i in range(5):
        cls = "filled" if i < filled else "empty"
        dots += f'<span class="dot {cls}"></span>'
    return dots


def independence_dots_html(ind_str):
    """Render the 5-dot independence meter."""
    filled = INDEPENDENCE_DOTS.get(ind_str, 0)
    dots = ""
    for i in range(5):
        cls = "filled" if i < filled else "empty"
        dots += f'<span class="dot {cls}"></span>'
    return dots


def sensor_card_html(sensor, family):
    """One catalog card. Shared by /catalog/ and /families/<slug>/ so the two
    renderings of the same entry cannot drift apart."""
    return f"""          <a class="signal-card" href="/sensors/{sensor['slug']}/">
            <div class="signal-card-meta">
              <span class="tag tag-family">{html.escape(family['name'])}</span>
              <span class="tag tag-type">{html.escape(sensor.get('type', '').title())}</span>
            </div>
            <h3 class="signal-card-title">{html.escape(sensor['title'])}</h3>
            <p class="signal-card-blurb">{html.escape(blurb_text(sensor.get('body_html', ''), 200))}</p>
            <div class="signal-card-footer">
              <span class="oracle-meter">{oracle_dots_html(sensor.get('oracle', 'low'))} Oracle</span>
              {latency_badge_html(sensor.get('latency', ''))}
            </div>
          </a>\n"""
