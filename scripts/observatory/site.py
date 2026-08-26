"""The build orchestrator: main().

The one place that knows what a full build is and in what order it happens.
Read top to bottom, it is the table of contents for the whole package."""

import shutil

from . import config
from .content import compute_backlinks, load_sensors, og_card_items
from .dates import catalog_as_of, first_seen_dates
from .feed import generate_rss
from .gates import assert_output_invariants, validate_sensors
from .llms import generate_llms_full_txt, generate_llms_txt
from .pages.about import generate_about_page
from .pages.atlas import generate_atlas_page
from .pages.catalog import generate_catalog_page
from .pages.categories import generate_categories_page
from .pages.contact import generate_contact_page
from .pages.families import generate_family_pages
from .pages.framework import generate_framework_page
from .pages.glossary import generate_glossary_page
from .pages.home import generate_index_page
from .pages.notfound import generate_404
from .pages.privacy import generate_privacy_page
from .pages.sensor import generate_sensor_page
from .search_index import generate_search_index
from .sitemap import generate_robots, generate_sitemap
from .taxonomy import FAMILIES, FAMILY_BY_SLUG


def main(check_only=False):
    print("Loading sensors...")
    sensors = load_sensors()
    print(f"  Found {len(sensors)} sensors")

    # GATES FIRST. Nothing below this line may write a file until every check
    # that can run on the loaded model has passed.
    validate_sensors(sensors)
    if check_only:
        print("Done (--check: validated, wrote nothing).")
        return

    # Build lookup tables
    sensors_by_id = {s["id"]: s for s in sensors}
    families_by_slug = FAMILY_BY_SLUG

    # Compute backlinks
    backlinks = compute_backlinks(sensors)
    for sid, bls in backlinks.items():
        print(f"  {sid}: {len(bls)} backlinks")

    output_dir = config.OUTPUT_DIR

    # Publication dates (git/first_seen.json) and the catalog's own reference
    # date. Computed once, passed down: every generator that renders a date
    # must render the same one, and none of them may look at the clock.
    published = first_seen_dates(sensors)
    as_of = catalog_as_of(sensors, published)
    print(f"  Catalog as of {as_of} (derived from content, not the clock)")

    # Remove stale output from the old /pages/*.html layout
    stale_pages = output_dir / "pages"
    if stale_pages.exists():
        shutil.rmtree(stale_pages)
    for stale in ("index.html",):
        pass  # index.html is still the root output, regenerated below

    (output_dir / "sensors").mkdir(parents=True, exist_ok=True)

    # Before the pages: each sensor page points og:image at its own card only
    # if that card exists on disk.
    print("Generating OG cards...")
    try:
        import gen_og
        og_result = gen_og.generate(og_card_items(sensors))
    except Exception as exc:  # never fail a build over a share image
        og_result = {"written": 0, "skipped": 0, "removed": 0, "error": str(exc)}
    print(f"  {og_result['written']} rendered, {og_result['skipped']} unchanged, "
          f"{og_result['removed']} removed")
    if og_result["error"]:
        print(f"  warning: {og_result['error']}")

    print("Generating search index...")
    generate_search_index(sensors, output_dir)
    print("  search-index.json")

    print("Generating sitemap and robots...")
    generate_sitemap(sensors, output_dir)
    print("  sitemap.xml")
    generate_robots(output_dir)
    print("  robots.txt")

    print("Generating RSS feed...")
    generate_rss(sensors, output_dir)
    print("  rss.xml")

    print("Generating 404 page...")
    generate_404(sensors, output_dir)
    print("  404.html")

    print("Generating llms.txt...")
    generate_llms_txt(sensors, output_dir)
    print("  llms.txt")

    # Copy markdown sources for content negotiation (Accept: text/markdown)
    md_dir = output_dir / "md" / "sensors"
    md_dir.mkdir(parents=True, exist_ok=True)
    for filepath in sorted((config.CONTENT_DIR / "sensors").glob("*.md")):
        shutil.copy2(filepath, md_dir / filepath.name)
    print("  md/sensors/*.md (for content negotiation)")

    print("Generating pages...")
    generate_index_page(sensors, output_dir)
    print("  index.html")

    generate_catalog_page(sensors, output_dir)
    print("  catalog/")

    generate_family_pages(sensors, output_dir)
    print(f"  families/ ({len(FAMILIES)} pages)")

    generate_atlas_page(sensors, output_dir)
    print("  atlas/")

    generate_framework_page(sensors, output_dir)
    print("  framework/")

    generate_about_page(output_dir)
    print("  about/")

    generate_contact_page(output_dir)
    print("  contact/")

    generate_privacy_page(output_dir)
    print("  privacy/")

    generate_glossary_page(output_dir)
    print("  glossary/")

    generate_categories_page(sensors, output_dir)
    print("  categories/")

    for sensor in sensors:
        generate_sensor_page(sensor, backlinks, sensors_by_id, families_by_slug,
                             output_dir, published=published, as_of=as_of)
        print(f"  sensors/{sensor['slug']}/")

    # After the pages: llms-full.txt folds in the framework and glossary as
    # this build rendered them.
    print("Generating llms-full.txt...")
    generate_llms_full_txt(sensors, output_dir, published=published)
    print("  llms-full.txt")

    print("Exporting catalog dataset...")
    import export_cli_data
    written = export_cli_data.export()
    print("  cli/data/sensors.json + sensors.json (%d sensors, %d families)" % written[:2])

    # Post-checks: these read generated HTML, so they cannot be gates. See
    # the "Gate ordering" comment above validate_sensors().
    assert_output_invariants(sensors, output_dir)

    print("Done.")
