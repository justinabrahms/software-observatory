"""Software Observatory — the static site generator, as a package.

This was one 4,059-line scripts/build.py. The split is by responsibility, not
by size; read them in roughly this order:

    config        paths and site constants (the test suite repoints these)
    taxonomy      families, stack layers, lifecycle stages, the scales
    render        markdown -> HTML, and the strings derived from rendered HTML
    content       loading the sensor corpus, backlinks, see_also resolution
    components    the small HTML fragments shared across pages
    jsonld        structured-data builders
    layout        the shared <head>/header/footer shell every page goes through
    review        review-provenance rendering
    dates         date normalization, first-seen dates, the catalog epoch
    pages/        one module per generated page
    search_index  search-index.json
    sitemap       sitemap.xml + robots.txt
    feed          rss.xml
    llms          llms.txt + llms-full.txt
    gates         everything that refuses to publish
    site          main(): the order a build happens in

scripts/build.py is the entry point and the compatibility surface: the other
scripts (check_frontmatter.py, export_cli_data.py, gen_og.py) import names
from it, and it re-exports them from here.
"""
