#!/usr/bin/env python3
"""Migrate Tooling and References sections from markdown body into structured frontmatter.

Parses the existing `## Tooling` and `## References` sections from each
content/sensors/*.md, extracts them into structured `references:` and `tools:`
lists in the YAML frontmatter, and removes the body sections.

Run once; idempotent (skips files that already have structured frontmatter).
"""
import glob
import re
import yaml
from pathlib import Path

SENSOR_DIR = Path(__file__).resolve().parent.parent / "content" / "sensors"

# Tool descriptions for known tools (manual curation)
TOOL_DESCRIPTIONS = {
    "Stryker": "Mutation testing for JavaScript/TypeScript",
    "mutmut": "Mutation testing for Python",
    "PIT": "Mutation testing for Java/JVM",
    "cargo-mutants": "Mutation testing for Rust",
    "GCC": "GNU Compiler Collection",
    "Clang": "LLVM C/C++/ObjC compiler",
    "rustc": "The Rust compiler",
    "tsc": "TypeScript compiler with type checking",
    "ESLint": "Pluggable JavaScript/TypeScript linter",
    "ruff": "Fast Python linter and formatter",
    "golangci-lint": "Go linter aggregator",
    "Semgrep": "Multi-language static analysis with custom rules",
    "CodeQL": "Semantic code analysis engine by GitHub",
    "Bandit": "Python security linter",
    "brakeman": "Static security analysis for Rails",
    "OpenAPI Validator": "Validate APIs against OpenAPI specs",
    "Terraform plan": "Infrastructure-as-code plan preview",
    "kubectl admission": "Kubernetes admission controllers",
    "sqlfluff": "SQL linter and formatter",
    "Pact": "Consumer-driven contract testing",
    "Spring Cloud Contract": "Contract testing for Spring/JVM",
    "Postman": "API testing and contract validation",
    "pytest": "Python testing framework",
    "Jest": "JavaScript testing framework",
    "JUnit": "Java testing framework",
    "Go testing": "Go's built-in testing package",
    "Testcontainers": "Integration testing with Docker containers",
    "Docker Compose": "Multi-container orchestration for testing",
    "Jest snapshot": "Snapshot testing for JavaScript",
    "Vitest": "Vite-native testing framework with snapshots",
    "instanbul": "JavaScript code coverage",
    "diff-cover": "Coverage for changed lines only",
    "Codecov": "Hosted code coverage reporting",
    "Coveralls": "Hosted code coverage reporting",
    "coverage.py": "Python code coverage measurement",
    "Istanbul": "JavaScript code coverage",
    "JaCoCo": "Java code coverage",
    "gcov": "GCC code coverage",
    "Great Expectations": "Python data quality testing",
    "Soda": "Data quality testing and monitoring",
    "dbt tests": "Data transformation testing",
    "DB constraints": "Database-level CHECK/FOREIGN KEY constraints",
    "CHECK constraints": "SQL CHECK constraints",
    "foreign keys": "Database referential integrity constraints",
    "pg_constraint": "PostgreSQL constraint catalog",
    "libFuzzer": "LLVM in-process fuzzer",
    "cargo-fuzz": "Fuzzing for Rust",
    "AFL++": "Coverage-guided fuzzer",
    "CIFuzz": "Continuous fuzzing integration for CI",
    "Hypothesis": "Property-based testing for Python",
    "QuickCheck": "Property-based testing for Haskell",
    "fast-check": "Property-based testing for TypeScript",
    "test.check": "Property-based testing for Clojure",
    "Csmith": "Random C program generator for compiler testing",
    "DifferentialFuzzer": "Differential fuzzing framework",
    "SQLancer": "Differential testing for SQL databases",
    "Chaos Mesh": "Kubernetes chaos engineering platform",
    "Gremlin": "Managed chaos engineering service",
    "Litmus": "Cloud-native chaos engineering",
    "Chaos Monkey": "Netflix's instance termination service",
    "Honeycomb": "Observability platform for high-cardinality events",
    "Lightstep": "Distributed tracing and observability",
    "OpenTelemetry": "Open-standard observability instrumentation",
    "Jaeger": "Distributed tracing backend",
    "Zipkin": "Distributed tracing system",
    "Tempo": "Grafana-backed distributed tracing",
    "Pyroscope": "Continuous profiling platform",
    "pprof": "Go profiling tool",
    "Parca": "Continuous profiling for Kubernetes",
    "Datadog Profiler": "Always-on profiling in Datadog",
    "Prometheus": "Metrics collection and alerting",
    "Datadog": "Cloud monitoring and observability",
    "Grafana": "Metrics visualization and dashboards",
    "CloudWatch": "AWS monitoring and metrics",
    "Kayenta": "Netflix's automated canary analysis",
    "Argo Rollouts": "Kubernetes progressive delivery",
    "Flagger": "Kubernetes progressive delivery and canary",
    "Envoy shadow": "Envoy proxy shadow traffic mirroring",
    "diffy": "Differential proxy for API testing",
    "go-shadow": "Go HTTP shadow traffic proxy",
    "Akka": "Actor framework for JVM concurrency",
    "grpcurl": "gRPC command-line client",
    "openapi-diff": "OpenAPI spec diff tool",
    "revapi": "API compatibility checking for JVM",
    "SLO dashboards": "Service level objective tracking dashboards",
    "error budget calculators": "Error budget tracking tools",
    "dependency-cruiser": "JavaScript/TypeScript dependency analysis",
    "import-linter": "Python import linting and boundary enforcement",
    "madge": "JavaScript dependency graph and circular dependency detection",
    "dependency-graph": "Gradle dependency graph plugin",
    "ArchUnit": "Architecture testing for Java",
    "NetArchTest": ".NET architecture rules testing",
    "CodeScene": "Code analysis predicting technical debt from behavioral code",
    "crux": "Code complexity analysis tool",
    "git-quick-stats": "Git history analysis script",
    "Istio": "Service mesh with traffic management and observability",
    "Linkerd": "Lightweight Kubernetes service mesh",
    "Cilium": "eBPF-based networking, observability, and security",
    "eBPF tools": "Kernel-level observability tools",
    "git log": "Git commit history",
    "Sentry": "Error tracking and crash reporting",
    "Jira correlation": "Incident-to-commit correlation via Jira",
    "Jira": "Project and issue tracking",
    "Linear": "Issue tracking for product teams",
    "incident.io": "Incident management and response platform",
    "GitHub PR review": "Pull request review on GitHub",
    "Gerrit": "Web-based code review for Git",
    "Reviewable": "Code review tool for GitHub PRs",
    "doctest": "Python doctest module",
    "rustdoc": "Rust documentation generator with doc tests",
    "TypeDoc": "TypeScript API documentation generator",
    "OpenAPI round-trip": "Validate OpenAPI spec against actual API responses",
    "ADRs": "Architecture Decision Records",
    "Conventional Commits": "Structured commit message specification",
    "git blame": "Git history annotation per line",
    "GitHub Actions": "CI/CD workflow automation",
    "GitLab CI": "GitLab's built-in CI/CD",
    "Jenkins": "Extensible automation server",
    "pre-commit hooks": "Pre-commit framework for git hooks",
    "Dafny": "Verification-aware programming language",
    "Frama-C": "Static analysis and verification for C",
    "JML": "Java Modeling Language for behavioral interface specifications",
    "Rust typestate": "Rust's type system encoding program states",
    "Liquid Haskell": "Haskell refinement type checking",
    "OPA Gatekeeper": "Kubernetes policy enforcement via Open Policy Agent",
    "Kyverno": "Kubernetes-native policy management",
    "Conftest": "Policy testing for structured data",
    "HashiCorp Sentinel": "Policy-as-code for Terraform",
    "cosign": "Container signing tool",
    "Sigstore": "Software supply chain signing",
    "in-toto": "Software supply chain integrity framework",
    "SLSA": "Supply chain security framework and attestation",
    "Bazel": "Google's build system",
    "Buck": "Meta's build system",
    "Nix": "Reproducible build system and package manager",
    "ccache": "Compiler cache for fast rebuilds",
    "LaunchDarkly": "Feature management platform",
    "Statsig": "Experimentation and feature flag platform",
    "GrowthBook": "Open-source feature flagging and A/B testing",
    "Unleash": "Open-source feature flag management",
    "DORA survey": "DORA research assessment survey",
    "DevOps Research Assessment": "DORA's four-metric assessment tool",
    "Kiali": "Service mesh observability for Istio",
    "Hubble": "eBPF-based network observability for Kubernetes",
    "smoke-tester": "Simple HTTP smoke testing",
    "curl-based smoke tests": "Basic HTTP endpoint checks via curl",
    "k6 smoke": "Smoke testing with k6 load testing tool",
    "Checkly": "Synthetic monitoring as code",
    "k6": "Open-source load testing tool",
    "Pingdom": "Uptime and performance monitoring",
    "Datadog Synthetic": "Synthetic monitoring in Datadog",
    "assertpy": "Python assertion library",
    "pytest-check": "Non-blocking assertions for pytest",
    "Hypothesis invariants": "Using Hypothesis for invariant checking",
    "OPA Gatekeeper": "Kubernetes policy enforcement via Open Policy Agent",
    "assertpy": "Python fluent assertion library",
}


def parse_frontmatter(filepath):
    txt = open(filepath).read()
    parts = txt.split("---", 2)
    if len(parts) < 3:
        return {}, txt, parts
    meta = yaml.safe_load(parts[1]) or {}
    return meta, parts[2], parts


def extract_section(body, heading):
    """Extract a ## heading section, returning (items, body_without_section)."""
    # Match the heading and everything until the next ## or end
    pattern = rf"## {re.escape(heading)}\s*\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, body, re.DOTALL)
    if not match:
        return [], body
    section_content = match.group(1).strip()
    # Remove the section from body
    body = body[:match.start()] + body[match.end():]
    # Parse list items
    items = []
    for line in section_content.split("\n"):
        line = line.strip()
        if not line or not line.startswith("-"):
            continue
        items.append(line.lstrip("- ").strip())
    return items, body


def parse_reference_line(line):
    """Parse a reference line into a structured dict."""
    ref = {}

    # Pattern: Title (Year, tier X) — URL
    m = re.match(r"(.+?)\s*\((\d{4}),\s*tier\s*([IV]+)\)\s*[—–-]\s*(https?://\S+)", line)
    if m:
        ref["title"] = m.group(1).strip().rstrip(".")
        ref["year"] = int(m.group(2))
        ref["tier"] = m.group(3)
        ref["url"] = m.group(4).strip()
        ref["kind"] = "paper"
        return ref

    # Pattern: Title: URL  (tool homepages)
    m = re.match(r"(.+?):\s*(https?://\S+)", line)
    if m:
        ref["title"] = m.group(1).strip()
        ref["url"] = m.group(2).strip()
        ref["kind"] = "tool" if not m.group(1).strip()[0].isupper() or "wikipedia" in m.group(2) else "tool"
        return ref

    # Pattern: Authors, 'Title' (Year)
    m = re.match(r"(.+?)['\u2019](.+?)['\u2019]\s*\((\d{4})\)", line)
    if m:
        ref["authors"] = m.group(1).strip()
        ref["title"] = m.group(2).strip()
        ref["year"] = int(m.group(3))
        ref["kind"] = "paper"
        return ref

    # Pattern: Title (Year)
    m = re.match(r"(.+?)\s*\((\d{4})\)", line)
    if m:
        ref["title"] = m.group(1).strip().rstrip(",")
        ref["year"] = int(m.group(2))
        ref["kind"] = "paper"
        return ref

    # Bare URL
    if line.startswith("http"):
        ref["url"] = line.strip()
        ref["kind"] = "other"
        return ref

    # Fallback: whole line is the title
    ref["title"] = line.strip()
    ref["kind"] = "other"
    return ref


def parse_tool_line(line):
    """Parse a tool line into a structured dict."""
    tool = {}
    tool["title"] = line.strip()
    tool["kind"] = "tool"
    tool["url"] = ""
    desc = TOOL_DESCRIPTIONS.get(line.strip())
    if desc:
        tool["description"] = desc
    return tool


def main():
    migrated = 0
    skipped = 0

    for filepath in sorted(SENSOR_DIR.glob("*.md")):
        meta, body, parts = parse_frontmatter(filepath)

        # Skip if already has structured references/tools
        if meta.get("references") or meta.get("tools"):
            print(f"  SKIP {filepath.name} — already has structured frontmatter")
            skipped += 1
            continue

        # Extract sections from body
        tool_items, body = extract_section(body, "Tooling")
        ref_items, body = extract_section(body, "References")

        if not tool_items and not ref_items:
            print(f"  SKIP {filepath.name} — no Tooling/References sections")
            skipped += 1
            continue

        # Parse into structured data
        tools = [parse_tool_line(item) for item in tool_items]
        refs = [parse_reference_line(item) for item in ref_items]

        # Merge: tools go into references list with kind=tool
        all_refs = refs + tools
        if not all_refs:
            print(f"  SKIP {filepath.name} — nothing parsed")
            skipped += 1
            continue

        # Clean up body: remove leading/trailing blank lines
        body = body.strip()
        while "\n\n\n" in body:
            body = body.replace("\n\n\n", "\n\n")

        # Rebuild frontmatter
        meta["references"] = all_refs
        fm = yaml.dump(meta, default_flow_style=False, sort_keys=False, allow_unicode=True)
        out = f"---\n{fm}---\n\n{body}\n"
        open(filepath, "w").write(out)
        print(f"  MIGRATED {filepath.name} — {len(refs)} refs + {len(tools)} tools")
        migrated += 1

    print(f"\nMigrated: {migrated}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
