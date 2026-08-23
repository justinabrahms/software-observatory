# Changelog

All notable changes to the Software Observatory catalog are documented here.
Dates are when the change was reviewed/published, not when the content was
originally written.

## 2026-08-23

### Added
- Glossary page (`pages/glossary.html`) with 16 core vocabulary entries,
  linked from the nav and from the catalog/about placeholder links.
- Categories index page (`pages/categories.html`) listing all non-family
  categories with their sensors.
- `sitemap.xml` and `robots.txt` generated at build time.
- Canonical URLs, Open Graph, Twitter Card, and meta description tags on
  all pages.
- JSON-LD structured data (`WebSite` + `Person`) on the homepage.
- `last_reviewed` field in every sensor frontmatter.
- "Reviewed" date in each sensor page's properties sidebar.
- Frontmatter validator (`scripts/check_frontmatter.py`) — validates all
  sensor frontmatter against the known constants in `build.py`.
- CI pipeline (`.github/workflows/build-check-deploy.yml`) — builds, runs
  frontmatter + link checks, and deploys on push to `main`.
- `CONTRIBUTING.md` at the repo root.
- `README.md` at the repo root.
- Author identity (Justin Abrahms) in the footer, about page, and README.

### Changed
- Homepage "recent entries" section renamed to "Recently reviewed" and
  sorted by `last_reviewed` date instead of filename order.
- About page Contributing section replaced with real content (was Lorem
  ipsum).
- Category links on sensor pages now point to `pages/categories.html#<slug>`
  instead of dead `#` anchors.

### Fixed
- 75 broken inter-sensor links found and fixed by the link checker.
- Catalog card blurbs now take the full first paragraph and decode HTML
  entities correctly.
