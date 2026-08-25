.PHONY: build check check-frontmatter check-links check-citations check-external \
        check-deploy cli-test deploy serve

PY := .venv/bin/python

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
build:
	$(PY) scripts/build.py

# ---------------------------------------------------------------------------
# Gates
#
# `make check` runs every gate CI runs, in the order CI runs them. If it is
# green locally, CI is green. Contributors should never have to remember which
# individual scripts to invoke — that is how check_frontmatter.py came to be
# mentioned in zero human-facing docs while silently gating every deploy.
#
# Order matters: the content-only checks run first because they are fast and
# catch the largest class of authoring mistakes, and there is no point building
# a site out of frontmatter that does not validate. check-links needs the
# generated HTML, so it runs after the build.
# ---------------------------------------------------------------------------
check: check-frontmatter check-citations build check-links cli-test check-deploy
	@echo "All gates passed."

check-frontmatter:
	$(PY) scripts/check_frontmatter.py

check-citations:
	$(PY) scripts/check_citations.py

check-links:
	$(PY) scripts/check_links.py

cli-test:
	node cli/test/smoke.mjs

# Network checks: slow, flaky under load, and rate-limited. Not part of `make
# check`; CI runs these on a weekly schedule and files an issue on failure.
check-external: build
	$(PY) scripts/check_links.py --external --ttl 30
	$(PY) scripts/check_citations.py --external --ttl 30

# ---------------------------------------------------------------------------
# Deploy manifest
#
# DEPLOY_PUBLIC is the allow-list: the only paths that reach the web server.
# DEPLOY_PRIVATE is everything that deliberately stays local. `check-deploy`
# fails if any top-level path in the worktree is in neither list, so a new
# directory cannot silently join the public site (which is how .github/,
# CHANGELOG.md and 16 MB of .crush/ agent transcripts ended up published) and a
# new generated section cannot silently fail to publish.
#
# archive-* directories are matched by prefix, below.
#
# When you cannot tell which list a path belongs in, put it in DEPLOY_PRIVATE.
# Wrong-private fails closed: a page 404s and check-links catches it. Wrong-
# public fails open: it is on the internet before anyone notices. `notes/` is
# classified private on exactly that basis — it appeared as an unreferenced
# markdown source with no renderer behind it. If it is meant to be published,
# move it up and say why.
# ---------------------------------------------------------------------------
DEPLOY_PUBLIC := \
  index.html 404.html llms.txt robots.txt rss.xml sitemap.xml search-index.json \
  favicon.svg og.png \
  LICENSE LICENSE-CODE LICENSE-CONTENT \
  css js pages \
  og \
  md \
  sensors catalog atlas framework about contact privacy glossary categories

DEPLOY_PRIVATE := \
  .git .gitignore .github .venv .browser-libs .crush .opencode .claude \
  .link-cache.json .citation-cache.json .opencode-review.md \
  __pycache__ .pytest_cache .DS_Store \
  content templates scripts cli results scratch \
  notes \
  Makefile AGENTS.md README.md CONTRIBUTING.md CHANGELOG.md TODO.md \
  abstract.md abstract.sh chat-w-gpt.md

check-deploy:
	@unclassified=""; \
	for f in $$(ls -A); do \
	  case "$$f" in archive-*) continue ;; esac; \
	  case " $(DEPLOY_PUBLIC) $(DEPLOY_PRIVATE) " in \
	    *" $$f "*) ;; \
	    *) unclassified="$$unclassified $$f" ;; \
	  esac; \
	done; \
	if [ -n "$$unclassified" ]; then \
	  echo "check-deploy: unclassified top-level path(s):$$unclassified"; \
	  echo "check-deploy: add each to DEPLOY_PUBLIC (it belongs on the site) or"; \
	  echo "check-deploy: DEPLOY_PRIVATE (it does not) in the Makefile. Refusing to"; \
	  echo "check-deploy: guess — guessing is what published .github/ and .crush/."; \
	  exit 1; \
	fi; \
	echo "check-deploy: deploy manifest covers every top-level path."

# ---------------------------------------------------------------------------
# Deploy
#
# ALLOW-LIST, not deny-list. Everything is excluded by the trailing
# --exclude='*' unless it was explicitly included above it; rsync takes the
# first matching rule. A deny-list fails open — anything nobody thought to
# exclude is published — which is how agent transcripts, the CI workflow and
# the changelog reached production.
#
# Note: --delete does NOT remove receiver files that match an exclude rule, so
# converting to an allow-list stops new leaks but does not clean up old ones.
# Already-leaked paths must be purged on the server by hand; see the deploy
# notes in the PR that introduced this.
#
# Publish to the observer@abrah.ms deploy slot. The `observer` user's only
# authorized key is pinned by `rrsync -wo` to /srv/softwareobservatory.com,
# so this key can write nowhere else on the host.
# ---------------------------------------------------------------------------
RSYNC_INCLUDES := $(foreach p,$(DEPLOY_PUBLIC),--include='/$(p)' --include='/$(p)/***')

deploy: check-deploy build
	rsync -avz --delete \
	  -e "ssh -i $$HOME/.ssh/softwareobservatory-deploy" \
	  $(RSYNC_INCLUDES) \
	  --exclude='*' \
	  ./ observer@abrah.ms:.
	@echo "Deployed to https://softwareobservatory.com"

serve:
	python3 -m http.server
