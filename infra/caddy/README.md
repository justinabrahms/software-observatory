# infra/caddy

The Caddy site block for softwareobservatory.com, tracked so that changes to
how the site is *served* go through review the same way changes to what it
serves do.

## This is a record, not a source

Nothing in this repo applies this file, and that is on purpose.

`make deploy` rsyncs to the `observer` user, whose single authorized key is
pinned by `rrsync -wo` to `/srv/softwareobservatory.com`. That key can write
static files and nothing else. If Caddy were pointed at an `import` inside that
directory, the deploy key would gain control of the web server's
configuration — CSP, TLS, redirects, every header — and the blast radius that
pinning exists to create would be gone. A leaked deploy key is currently a
defaced page; it would become a hostile origin.

So the file is applied by hand, and a check keeps it honest.

## Verifying

```sh
CADDY_HOST=user@example make check-caddy
```

Read-only: one `ssh <host> cat /etc/caddy/Caddyfile`, no sudo (the file is
0644), no writes. It compares the live site block against this one, ignoring
comments, blank lines and the `tls` stanza, and exits non-zero on any
difference. The host is not recorded here — public files in this repo carry no
hostnames — it is in `OPERATIONS.md`.

Not wired into `make check`: CI holds only the rsync-pinned deploy key, so it
cannot read the server's config and would fail the gate for the wrong reason.

## Applying a change

Edit here first, get it reviewed, then on the server:

```sh
sudo cp -a /etc/caddy/Caddyfile /etc/caddy/Caddyfile.bak.pre-<change>-$(date +%s)
sudo $EDITOR /etc/caddy/Caddyfile          # paste the block, restoring the tls stanza
sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
sudo systemctl reload caddy
CADDY_HOST=user@example make check-caddy   # confirm repo and server agree again
```

`validate` before `reload`, always: a reload with a bad config leaves the old
one running, but a restart with one does not, and the two are one typo apart.
The live Caddyfile holds 32 site blocks for unrelated services; only this one
belongs to this repo, which is the other reason the whole file is not tracked.

## What the tls stanza holds back

The live block issues certificates over DNS-01 rather than HTTP-01, so a cert
never waits on A-record propagation. The provider and its credential
environment variable are named in `OPERATIONS.md` (untracked) and nowhere in a
tracked file. Substituting that stanza is what turns this record back into a
working config.
