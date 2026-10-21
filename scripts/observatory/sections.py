"""Required editorial sections, checked before the publication build (#108)."""

from html.parser import HTMLParser

import markdown

REQUIRED_SECTIONS = (
    "In practice", "How it gets gamed", "Response playbook", "What it cannot detect",
)


class _Sections(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections = {}
        self.current = None
        self.heading = None

    def handle_starttag(self, tag, attrs):
        if tag == "h2":
            self.current = None
            self.heading = []

    def handle_data(self, data):
        if self.heading is not None:
            self.heading.append(data)
        elif self.current and data.strip():
            self.sections[self.current] = True

    def handle_endtag(self, tag):
        if tag == "h2" and self.heading is not None:
            self.current = "".join(self.heading).strip()
            self.sections.setdefault(self.current, False)
            self.heading = None


def section_errors(body):
    # Parse rendered headings so examples containing `##` inside code fences
    # cannot satisfy the gate. Comments and markup alone are not section text.
    parser = _Sections()
    parser.feed(markdown.markdown(body, extensions=["fenced_code", "tables"]))
    return [
        f"missing or empty section '## {title}'"
        for title in REQUIRED_SECTIONS if not parser.sections.get(title)
    ]
