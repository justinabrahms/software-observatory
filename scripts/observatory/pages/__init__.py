"""One module per generated page.

Every module here exposes a single generate_*(…, output_dir) function that
writes exactly the page it is named for. They share the shell (layout),
the fragments (components), the structured data (jsonld) and the taxonomy;
they do not import each other.
"""
