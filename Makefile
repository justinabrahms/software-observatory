.PHONY: build deploy check serve cli-test

build:
	.venv/bin/python scripts/build.py

check:
	.venv/bin/python scripts/check_links.py

cli-test:
	node cli/test/smoke.mjs

# Publish to the observer@abrah.ms deploy slot. The `observer` user's only
# authorized key is pinned by `rrsync -wo` to /srv/softwareobservatory.com,
# so this key can write nowhere else on the host.
deploy: build
	rsync -avz --delete \
	  -e "ssh -i $$HOME/.ssh/softwareobservatory-deploy" \
	  --exclude='.git/' \
	  --exclude='.venv/' \
	  --exclude='.browser-libs/' \
	  --exclude='content/' \
	  --exclude='templates/' \
	  --exclude='archive-*/' \
	  --exclude='scripts/' \
	  --exclude='cli/' \
	  --exclude='Makefile' \
	  --exclude='.gitignore' \
	  --exclude='AGENTS.md' \
	  ./ observer@abrah.ms:.
	@echo "Deployed to https://softwareobservatory.com"

serve:
	python3 -m http.server
