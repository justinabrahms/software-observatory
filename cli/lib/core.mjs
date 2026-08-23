import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const DATA_PATH = fileURLToPath(new URL("../data/sensors.json", import.meta.url));

let cache = null;

export function loadData() {
  if (!cache) {
    cache = JSON.parse(readFileSync(DATA_PATH, "utf8"));
  }
  return cache;
}

export function siteUrl(path = "") {
  const base = loadData().site.replace(/\/$/, "");
  return path ? `${base}/${path.replace(/^\//, "")}` : base;
}

export function listFamilies() {
  return loadData().families;
}

export function getFamily(slug) {
  const normalized = String(slug).toLowerCase();
  return loadData().families.find((f) => f.slug === normalized) || null;
}

export function listSensors({ family } = {}) {
  const { sensors } = loadData();
  if (!family) return sensors;
  const normalized = String(family).toLowerCase();
  return sensors.filter((s) => s.family === normalized);
}

export function findSensor(query) {
  const { sensors } = loadData();
  const normalized = String(query).toLowerCase();
  return (
    sensors.find((s) => s.id.toLowerCase() === normalized) ||
    sensors.find((s) => s.slug === normalized) ||
    sensors.find((s) => s.title.toLowerCase() === normalized) ||
    null
  );
}

export function getRelated(sensor) {
  const related = [];
  for (const id of sensor.see_also_ids) {
    const target = findSensor(id);
    if (target) {
      related.push({ kind: "sensor", id: target.id, slug: target.slug, title: target.title, family: target.family });
    }
  }
  for (const slug of sensor.see_also_families) {
    const family = getFamily(slug);
    if (family) {
      related.push({ kind: "family", slug: family.slug, name: family.name });
    }
  }
  for (const page of sensor.see_also_pages) {
    related.push({ kind: "page", ref: page });
  }
  return related;
}

export function listValues(field) {
  const values = new Set();
  for (const sensor of loadData().sensors) {
    const value = sensor.frontmatter[field];
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      for (const item of value) values.add(String(item));
    } else {
      values.add(String(value));
    }
  }
  return [...values].sort();
}

const STOPWORDS = new Set([
  "the", "and", "for", "are", "but", "not", "you", "your", "yours", "all", "any",
  "can", "could", "should", "would", "will", "shall", "may", "might", "must",
  "our", "ours", "their", "theirs", "his", "her", "hers", "its", "this", "that",
  "these", "those", "there", "here", "what", "when", "where", "which", "who",
  "whom", "why", "how", "has", "have", "had", "having", "does", "did", "doing",
  "done", "was", "were", "been", "being", "with", "from", "into", "onto", "upon",
  "about", "after", "before", "between", "through", "during", "without", "within",
  "they", "them", "then", "than", "too", "very", "just", "still", "even", "also",
  "know", "make", "made", "get", "got", "use", "used", "using", "want", "need",
]);

export function suggestSensors(question, { limit = 5 } = {}) {
  const { sensors, families } = loadData();
  const terms = String(question)
    .toLowerCase()
    .split(/[^\w]+/)
    .filter((t) => t.length >= 3 && !STOPWORDS.has(t));
  if (terms.length === 0) return [];

  const scored = [];
  for (const sensor of sensors) {
    const title = sensor.title.toLowerCase();
    const family = getFamily(sensor.family);
    const familyText = family ? `${family.name} ${family.question} ${family.examples}`.toLowerCase() : "";
    let score = 0;
    for (const term of terms) {
      if (title.includes(term)) score += 6;
      if (familyText.includes(term)) score += 2;
      if (sensor.body_text.includes(term)) score += 1;
    }
    if (score > 0) scored.push({ sensor, score });
  }
  scored.sort((a, b) => b.score - a.score || a.sensor.slug.localeCompare(b.sensor.slug));

  const seenFamilies = new Set();
  return scored.slice(0, limit).map(({ sensor, score }) => {
    const matched = terms.filter(
      (t) => sensor.title.toLowerCase().includes(t) || sensor.body_text.includes(t)
    );
    const firstOfFamily = !seenFamilies.has(sensor.family);
    seenFamilies.add(sensor.family);
    return {
      id: sensor.id,
      slug: sensor.slug,
      title: sensor.title,
      family: sensor.family,
      score,
      matched_terms: matched,
      gap: firstOfFamily,
      url: siteUrl(sensor.url_path),
    };
  });
}

export function stackCoverage(ids) {
  const { sensors, families } = loadData();
  const selected = [];
  const unknown = [];
  for (const id of ids) {
    const sensor = findSensor(id);
    if (sensor) selected.push(sensor);
    else unknown.push(id);
  }

  const coveredFamilies = new Map();
  const stackLevels = new Map();
  const oracles = new Map();
  const latencies = new Map();
  const types = new Map();
  for (const sensor of selected) {
    coveredFamilies.set(sensor.family, (coveredFamilies.get(sensor.family) || 0) + 1);
    const fm = sensor.frontmatter;
    if (fm.stack_level) stackLevels.set(fm.stack_level, (stackLevels.get(fm.stack_level) || 0) + 1);
    if (fm.oracle) oracles.set(fm.oracle, (oracles.get(fm.oracle) || 0) + 1);
    if (fm.latency) latencies.set(fm.latency, (latencies.get(fm.latency) || 0) + 1);
    if (fm.type) types.set(fm.type, (types.get(fm.type) || 0) + 1);
  }

  const missing = families.filter((f) => !coveredFamilies.has(f.slug));
  const recommendations = [];
  for (const family of missing.slice(0, 3)) {
    const candidate = sensors.find((s) => s.family === family.slug);
    if (candidate) {
      recommendations.push({
        id: candidate.id,
        slug: candidate.slug,
        title: candidate.title,
        family: candidate.family,
        reason: `covers the ${family.name} family ("${family.question}")`,
      });
    }
  }

  return {
    selected: selected.map((s) => ({ id: s.id, slug: s.slug, title: s.title, family: s.family })),
    unknown_ids: unknown,
    coverage: {
      families: Object.fromEntries(coveredFamilies),
      stack_levels: Object.fromEntries(stackLevels),
      oracle: Object.fromEntries(oracles),
      latency: Object.fromEntries(latencies),
      type: Object.fromEntries(types),
    },
    missing_families: missing.map((f) => ({ slug: f.slug, name: f.name, question: f.question })),
    recommendations,
  };
}
