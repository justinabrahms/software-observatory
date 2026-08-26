import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const DATA_PATH = fileURLToPath(new URL("../data/sensors.json", import.meta.url));
const PACKAGE_PATH = fileURLToPath(new URL("../package.json", import.meta.url));

export const CLI_VERSION = JSON.parse(readFileSync(PACKAGE_PATH, "utf8")).version;

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

// Every frontmatter key present anywhere in the dataset. `values <field>` uses
// this to reject an unknown field instead of returning an empty list, which an
// agent cannot distinguish from "this field has no values".
export function listFields() {
  const fields = new Set();
  for (const sensor of loadData().sensors) {
    for (const key of Object.keys(sensor.frontmatter)) fields.add(key);
  }
  return [...fields].sort();
}

// Common English plus the connective vocabulary people use to describe a
// symptom ("we keep shipping X", "our tests still fail"). These carry no
// signal about which sensor answers the question, and left in they dominate
// the ranking because they appear in every entry.
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
  "a", "an", "as", "at", "be", "by", "do", "if", "in", "is", "it", "me", "my",
  "no", "of", "off", "on", "or", "out", "over", "own", "re", "so", "to", "up",
  "us", "we", "ll", "ve", "same", "some", "such", "only", "more", "most",
  "other", "another", "each", "every", "both", "keep", "keeps", "kept", "go",
  "goes", "going", "lot", "lots", "one", "two", "let", "lets", "really", "new",
  "thing", "things", "stuff", "way", "ways", "help", "problem", "problems",
]);

// Light suffix stripping so a symptom sentence written in one tense matches an
// entry written in another: "shipping" -> "ship", "tests" -> "test",
// "regressions" -> "regression". Deliberately conservative -- "pass" must not
// become "pas", or it stops matching anything.
function stem(term) {
  if (term.length <= 3) return term;
  let out = term;
  if (out.endsWith("ies") && out.length > 4) return out.slice(0, -3) + "y";
  if (out.endsWith("sses")) return out.slice(0, -2);
  if (out.endsWith("ing") && out.length > 5) out = out.slice(0, -3);
  else if (out.endsWith("ed") && out.length > 4) out = out.slice(0, -2);
  else if (out.endsWith("es") && out.length > 4 && !/([sxz]|[cs]h)es$/.test(out)) out = out.slice(0, -2);
  else if (out.endsWith("s") && !out.endsWith("ss") && out.length > 3) out = out.slice(0, -1);
  if (/([bdfgklmnprt])\1$/.test(out)) out = out.slice(0, -1);
  return out;
}

// Word-start matching, not substring. Substring matching is why "pass" used to
// hit the "pass" inside unrelated prose and why two-letter tokens like "ai"
// matched the "ai" in "Time-to-Repair". A word-start match still lets "test"
// find "testing" and "mutation" find "Mutation Testing".
const TERM_RE_CACHE = new Map();
function termRegExp(term) {
  let re = TERM_RE_CACHE.get(term);
  if (!re) {
    re = new RegExp("(?:^|[^a-z0-9])" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "g");
    TERM_RE_CACHE.set(term, re);
  }
  re.lastIndex = 0;
  return re;
}

function countHits(text, term) {
  const re = termRegExp(term);
  let n = 0;
  while (re.exec(text) !== null) {
    n += 1;
    if (n >= 6) break;
  }
  return n;
}

// A match in what the entry is *about* outranks an incidental mention. The
// lede -- the opening paragraph, which is where every entry states the question
// it answers -- outranks the title, because someone describing a symptom is
// describing the question, not the name of the sensor. A deep body mention is
// worth almost nothing.
const FIELD_WEIGHTS = {
  lede: 60,
  title: 34,
  slug: 28,
  stack_level: 26,
  categories: 20,
  notes: 18,
  family: 18,
  body: 6,
};
const LEDE_CHARS = 320;
const NOTE_FIELDS = [
  "oracle_note", "independence_note", "scope_note",
  "latency_note", "actionability_note", "type_note",
];

let searchIndex = null;
function buildIndex() {
  if (searchIndex) return searchIndex;
  const { sensors } = loadData();
  const documents = sensors.map((sensor) => {
    const fm = sensor.frontmatter;
    const family = getFamily(sensor.family);
    return {
      sensor,
      lede: sensor.body_text.slice(0, LEDE_CHARS).toLowerCase(),
      title: sensor.title.toLowerCase(),
      slug: sensor.slug.replace(/-/g, " "),
      stack_level: String(fm.stack_level || "").replace(/-/g, " ").toLowerCase(),
      categories: (fm.categories || []).join(" ").toLowerCase(),
      notes: NOTE_FIELDS.map((k) => fm[k] || "").join(" ").toLowerCase(),
      family: family ? `${family.name} ${family.question} ${family.examples}`.toLowerCase() : "",
      body: sensor.body_text.toLowerCase(),
    };
  });
  searchIndex = { documents, idf: new Map() };
  return searchIndex;
}

// Inverse document frequency. "test" appears in nearly every entry in a catalog
// of test sensors, so it should barely move the ranking; "mutation" appears in
// a handful, so it should move it a lot. This is what stops a symptom sentence
// full of common catalog vocabulary from recommending whichever entry happens
// to have that vocabulary in its title.
function inverseDocumentFrequency(index, term) {
  let value = index.idf.get(term);
  if (value === undefined) {
    const total = index.documents.length;
    let seen = 0;
    for (const doc of index.documents) {
      if (countHits(doc.body, term) || countHits(doc.title, term) || countHits(doc.slug, term)) seen += 1;
    }
    value = Math.log(1 + total / (1 + seen)) / Math.log(1 + total);
    index.idf.set(term, value);
  }
  return value;
}

function questionTerms(question) {
  const words = String(question).toLowerCase().split(/[^a-z0-9+#]+/).filter(Boolean);
  const terms = new Map(); // stem -> first original word that produced it
  for (const word of words) {
    if (word.length < 2 || STOPWORDS.has(word)) continue;
    const key = stem(word);
    if (!terms.has(key)) terms.set(key, word);
  }
  return terms;
}

export function suggestSensors(question, { limit = 5 } = {}) {
  const index = buildIndex();
  const terms = questionTerms(question);
  if (terms.size === 0) return [];

  const scored = [];
  for (const doc of index.documents) {
    let score = 0;
    const matched = [];
    for (const [term, word] of terms) {
      let weight = 0;
      if (countHits(doc.lede, term)) {
        weight = FIELD_WEIGHTS.lede;
        if (countHits(doc.title, term)) weight += 20;
      } else if (countHits(doc.title, term)) weight = FIELD_WEIGHTS.title;
      else if (countHits(doc.slug, term)) weight = FIELD_WEIGHTS.slug;
      else if (countHits(doc.stack_level, term)) weight = FIELD_WEIGHTS.stack_level;
      else if (countHits(doc.categories, term)) weight = FIELD_WEIGHTS.categories;
      else if (countHits(doc.notes, term)) weight = FIELD_WEIGHTS.notes;
      else if (countHits(doc.family, term)) weight = FIELD_WEIGHTS.family;
      else {
        const n = countHits(doc.body, term);
        if (n) weight = FIELD_WEIGHTS.body + Math.min(n - 1, 4) * 2;
      }
      if (!weight) continue;
      // Covering another distinct term of the question is worth more than
      // hitting the same one again, so each match carries a coverage bonus.
      score += (weight + 18) * inverseDocumentFrequency(index, term);
      matched.push(word);
    }
    if (matched.length > 0) scored.push({ sensor: doc.sensor, score, matched });
  }
  scored.sort((a, b) => b.score - a.score || a.sensor.slug.localeCompare(b.sensor.slug));

  const seenFamilies = new Set();
  return scored.slice(0, limit).map(({ sensor, score, matched }) => {
    const firstOfFamily = !seenFamilies.has(sensor.family);
    seenFamilies.add(sensor.family);
    return {
      id: sensor.id,
      slug: sensor.slug,
      title: sensor.title,
      family: sensor.family,
      score: Math.round(score),
      matched_terms: matched,
      // How this result was produced. Today the only path is the term scorer;
      // a curated symptom -> sensor map would report "curated" here so a caller
      // can tell an authored recommendation from a keyword guess.
      basis: "keyword",
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

  // The only theory of composition here is "one sensor from each family", and
  // within a family the pick is the first entry in file order -- not a ranking.
  // Say so, and list the family's other entries, rather than presenting an
  // arbitrary pick as a considered recommendation. Composing by distinct doubt
  // eliminated (rather than by family) is the open question in issue #101.
  const missing = families.filter((f) => !coveredFamilies.has(f.slug));
  const recommendations = [];
  for (const family of missing.slice(0, 3)) {
    const candidates = sensors.filter((s) => s.family === family.slug);
    const candidate = candidates[0];
    if (candidate) {
      recommendations.push({
        id: candidate.id,
        slug: candidate.slug,
        title: candidate.title,
        family: candidate.family,
        basis: "family-coverage",
        reason:
          `nothing in this set covers the ${family.name} family ("${family.question}"). ` +
          `Listed as an example entry point, not a ranked pick: this is the first entry ` +
          `in the family, and any of its ${candidates.length} entries would close the same gap.`,
        alternatives: candidates.slice(1).map((s) => ({ id: s.id, slug: s.slug, title: s.title })),
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
    composition_rule: {
      id: "one-per-family",
      description:
        "Coverage is scored as one sensor per family. It does not model whether two sensors " +
        "eliminate the same doubt, so a set can look complete and still leave a doubt standing.",
    },
    recommendations,
  };
}
