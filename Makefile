.PHONY: build deploy check serve

build:
	.venv/bin/python build.py

check:
	.venv/bin/python check_links.py

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
	  --exclude='build.py' \
	  --exclude='check_links.py' \
	  --exclude='Makefile' \
	  --exclude='TODO.md' \
	  --exclude='chat-w-gpt.md' \
	  --exclude='AGENTS.md' \
	  ./ observer@abrah.ms:.
	@echo "Deployed to https://softwareobservatory.com"

serve:
	python3 -m http.server
