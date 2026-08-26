#!/usr/bin/env node
import {
  CLI_VERSION,
  loadData,
  siteUrl,
  listFamilies,
  getFamily,
  listSensors,
  findSensor,
  getRelated,
  listValues,
  listFields,
  suggestSensors,
  stackCoverage,
} from "../lib/core.mjs";
import { startMcpServer } from "../lib/mcp.mjs";

const USAGE = `softwareobservatory - query the Software Observatory sensor catalog

Usage: softwareobservatory [--json] [--plain] <command> [args]

Commands:
  list [--family <slug>]        List sensors (all, or within one family)
  families                      List the sensor families
  get <id|slug|title>           Show one sensor in full, with related entries
  search <term...>              Substring search over titles and entry text
  values <field>                Distinct frontmatter values (oracle, latency, type, ...)
  suggest <question...>         Suggest sensors relevant to a concern
  gaps <question...>            Like suggest, but only the family-coverage gaps
  stack <id,slug,...>           Family/stack coverage report for a sensor set
  mcp                           Run an MCP (stdio JSON-RPC) server for agents
  version                       Print CLI and dataset versions
  help                          This message

Flags:
  --json         Machine-readable output (full precision; stable for agents)
  --plain        Force human-readable output (default when stdout is a TTY)
  --help, -h     This message

Unknown flags, unknown commands, missing flag values and stray arguments are
errors (exit 1), never silently ignored. In JSON mode errors are written to
stderr as JSON.
`;

const BOOLEAN_FLAGS = ["--json", "--plain", "--help", "-h"];
const VALUE_FLAGS = ["--family"];
const ALL_FLAGS = [...BOOLEAN_FLAGS, ...VALUE_FLAGS];

// The contract for every command: which flags it accepts and how many
// positional arguments it takes. Anything outside the contract is an error.
// Silently dropping an argument -- which is how `list --familly structural`
// came to return all 59 sensors and exit 0 -- is the failure mode this catalog
// exists to warn about.
const COMMANDS = {
  list: { flags: ["--family"], min: 0, max: 0, usage: "list [--family <slug>]" },
  families: { flags: [], min: 0, max: 0, usage: "families" },
  get: { flags: [], min: 1, max: Infinity, usage: "get <id|slug|title>" },
  search: { flags: [], min: 1, max: Infinity, usage: "search <term...>" },
  values: { flags: [], min: 1, max: 1, usage: "values <field>" },
  suggest: { flags: [], min: 1, max: Infinity, usage: "suggest <question...>" },
  gaps: { flags: [], min: 1, max: Infinity, usage: "gaps <question...>" },
  stack: { flags: [], min: 1, max: Infinity, usage: "stack <id,slug,...>" },
  mcp: { flags: [], min: 0, max: 0, usage: "mcp" },
  version: { flags: [], min: 0, max: 0, usage: "version" },
  help: { flags: [], min: 0, max: 0, usage: "help" },
};
const COMMAND_NAMES = Object.keys(COMMANDS);

function levenshtein(a, b) {
  let previous = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i += 1) {
    const current = [i];
    for (let j = 1; j <= b.length; j += 1) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      current[j] = Math.min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost);
    }
    previous = current;
  }
  return previous[b.length];
}

// Nearest valid spelling, if there is one close enough to be worth offering.
function nearest(word, candidates) {
  let best = null;
  let bestDistance = Infinity;
  for (const candidate of candidates) {
    const distance = levenshtein(word, candidate);
    if (distance < bestDistance) {
      bestDistance = distance;
      best = candidate;
    }
  }
  return bestDistance <= (word.length <= 4 ? 1 : 2) ? best : null;
}

function hint(suggestion) {
  return suggestion ? ` Did you mean '${suggestion}'?` : "";
}

// Errors go to stderr in both modes. In JSON mode they are machine-readable, so
// an agent can parse the failure instead of parsing a valid-looking success.
function fail(jsonMode, payload, message, { usage = false } = {}) {
  if (jsonMode) {
    process.stderr.write(JSON.stringify({ ...payload, message }) + "\n");
  } else {
    console.error(message);
    if (usage) process.stderr.write("\n" + USAGE);
  }
  process.exit(1);
}

function parseArgv(argv) {
  const flags = { json: false, plain: false, help: false, family: null };
  const used = new Set();
  const positionals = [];
  const errors = [];
  let literal = false;

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (literal) {
      positionals.push(arg);
      continue;
    }
    if (arg === "--") {
      literal = true;
      continue;
    }
    if (!arg.startsWith("-")) {
      positionals.push(arg);
      continue;
    }

    let name = arg;
    let value = null;
    if (arg.startsWith("--") && arg.includes("=")) {
      const eq = arg.indexOf("=");
      name = arg.slice(0, eq);
      value = arg.slice(eq + 1);
    }

    if (!ALL_FLAGS.includes(name)) {
      const guess = nearest(name, ALL_FLAGS);
      errors.push({
        error: "unknown flag",
        flag: name,
        did_you_mean: guess || undefined,
        message: `Unknown flag '${name}'.${hint(guess)} Run 'softwareobservatory help' for usage.`,
      });
      continue;
    }
    if (used.has(name)) {
      errors.push({
        error: "repeated flag",
        flag: name,
        message: `Flag '${name}' was given more than once.`,
      });
      continue;
    }
    used.add(name);

    if (BOOLEAN_FLAGS.includes(name)) {
      if (value !== null) {
        errors.push({
          error: "unexpected flag value",
          flag: name,
          message: `Flag '${name}' does not take a value.`,
        });
        continue;
      }
      if (name === "--json") flags.json = true;
      else if (name === "--plain") flags.plain = true;
      else flags.help = true;
      continue;
    }

    if (value === null) {
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("-")) {
        errors.push({
          error: "missing flag value",
          flag: name,
          message: `Flag '${name}' requires a value, e.g. '${name} structural'.`,
        });
        continue;
      }
      value = next;
      i += 1;
    }
    if (value === "") {
      errors.push({
        error: "missing flag value",
        flag: name,
        message: `Flag '${name}' requires a non-empty value.`,
      });
      continue;
    }
    if (name === "--family") flags.family = value;
  }

  return { flags, used, positionals, errors };
}

// Resolve argv into a validated (command, args, flags) triple, or exit 1.
function resolveInvocation(argv) {
  const { flags, used, positionals, errors } = parseArgv(argv);
  const jsonMode = flags.plain ? false : flags.json || !process.stdout.isTTY;
  const [command, ...args] = positionals;

  if (flags.help) {
    process.stdout.write(USAGE);
    process.exit(0);
  }
  if (!command) {
    process.stderr.write(USAGE);
    process.exit(1);
  }
  if (flags.json && flags.plain) {
    fail(jsonMode, { error: "conflicting flags", flags: ["--json", "--plain"] },
      "Flags '--json' and '--plain' conflict; pass at most one.");
  }
  if (!Object.prototype.hasOwnProperty.call(COMMANDS, command)) {
    const guess = nearest(command, COMMAND_NAMES);
    fail(jsonMode, { error: "unknown command", command, did_you_mean: guess || undefined },
      `Unknown command '${command}'.${hint(guess)}`, { usage: true });
  }
  const spec = COMMANDS[command];

  if (errors.length > 0) {
    const first = errors[0];
    fail(jsonMode, { error: first.error, flag: first.flag, did_you_mean: first.did_you_mean }, first.message);
  }

  for (const flag of used) {
    if (BOOLEAN_FLAGS.includes(flag)) continue;
    if (!spec.flags.includes(flag)) {
      const accepted = [...spec.flags, "--json", "--plain"].join(", ");
      fail(jsonMode, { error: "flag not valid for command", flag, command, accepted_flags: [...spec.flags, "--json", "--plain"] },
        `Flag '${flag}' is not valid for '${command}'. '${command}' accepts: ${accepted}.`);
    }
  }

  if (args.length < spec.min) {
    fail(jsonMode, { error: "missing argument", command, usage: `softwareobservatory ${spec.usage}` },
      `Usage: softwareobservatory ${spec.usage}`);
  }
  if (args.length > spec.max) {
    const extra = args[spec.max];
    const guess = command === "list" && getFamily(extra) ? `--family ${extra}` : null;
    fail(jsonMode, { error: "unexpected argument", command, argument: extra, did_you_mean: guess || undefined, usage: `softwareobservatory ${spec.usage}` },
      `Unexpected argument '${extra}' for '${command}'.${hint(guess)} Usage: softwareobservatory ${spec.usage}`);
  }

  return { flags: { ...flags, json: jsonMode }, command, args };
}

function emit(flags, data, renderHuman) {
  if (flags.json) {
    process.stdout.write(JSON.stringify(data, null, 2) + "\n");
  } else {
    renderHuman(data);
  }
}

function sensorSummary(sensor) {
  return {
    id: sensor.id,
    slug: sensor.slug,
    title: sensor.title,
    family: sensor.family,
    url: siteUrl(sensor.url_path),
  };
}

function searchSensors(terms) {
  const needle = terms.join(" ").toLowerCase();
  if (!needle) return [];
  return loadData().sensors.filter(
    (s) => s.title.toLowerCase().includes(needle) || s.body_text.toLowerCase().includes(needle)
  );
}

function scoreSearch(sensor, needle) {
  let score = 0;
  if (sensor.title.toLowerCase().includes(needle)) score += 10;
  const occurrences = sensor.body_text.toLowerCase().split(needle).length - 1;
  return score + Math.min(occurrences, 5);
}

function snippet(sensor, needle) {
  const index = sensor.body_text.toLowerCase().indexOf(needle);
  if (index === -1) return sensor.body_text.slice(0, 120).trim() + "...";
  const start = Math.max(0, index - 60);
  const end = Math.min(sensor.body_text.length, index + needle.length + 60);
  return (start > 0 ? "..." : "") + sensor.body_text.slice(start, end).trim() + (end < sensor.body_text.length ? "..." : "");
}

function humanList(sensors) {
  let currentFamily = null;
  for (const sensor of sensors) {
    if (sensor.family !== currentFamily) {
      currentFamily = sensor.family;
      const family = getFamily(currentFamily);
      console.log(`\n${family ? family.name : currentFamily}`);
    }
    console.log(`  ${sensor.id.padEnd(9)} ${sensor.title}  (${sensor.slug})`);
  }
  console.log(`\n${sensors.length} sensor(s)`);
}

function humanFamilies(families) {
  for (const family of families) {
    console.log(`${family.num}. ${family.name} [${family.slug}] - ${family.question}`);
    console.log(`   ${family.count} sensor(s). Examples: ${family.examples}`);
  }
}

function humanGet(sensor, related) {
  console.log(`${sensor.title} (${sensor.id})`);
  console.log(`Family: ${sensor.family}  |  ${siteUrl(sensor.url_path)}`);
  console.log("");
  const fm = sensor.frontmatter;
  const rows = [
    ["Oracle strength", fm.oracle],
    ["Independence", fm.independence],
    ["Scope", fm.scope],
    ["Feedback latency", fm.latency],
    ["Actionability", fm.actionability],
    ["Type", fm.type],
    ["Stack level", fm.stack_level],
  ];
  for (const [label, value] of rows) {
    if (value) console.log(`  ${label.padEnd(18)} ${value}`);
  }
  console.log("");
  console.log(sensor.body_text);
  if (related.length > 0) {
    console.log("\nRelated:");
    for (const rel of related) {
      if (rel.kind === "sensor") console.log(`  - ${rel.title} (${rel.id})`);
      else if (rel.kind === "family") console.log(`  - ${rel.name} family [${rel.slug}]`);
      else console.log(`  - page: ${rel.ref}`);
    }
  }
}

function humanSuggest(results, { gapsOnly }) {
  const shown = gapsOnly ? results.filter((r) => r.gap) : results;
  for (const result of shown) {
    const marker = result.gap ? "GAP " : "    ";
    console.log(
      `${marker}${result.id.padEnd(9)} ${result.title} [${result.family}]  matched: ${result.matched_terms.join(", ") || "-"}`
    );
  }
  if (shown.length === 0) console.log("No suggestions. Try different wording.");
  else console.log(`\n${shown.length} suggestion(s)`);
}

function humanStack(report) {
  console.log(`Stack: ${report.selected.length} sensor(s)`);
  for (const sensor of report.selected) {
    console.log(`  - ${sensor.title} (${sensor.id}) [${sensor.family}]`);
  }
  if (report.unknown_ids.length > 0) {
    console.log(`\nUnknown ids: ${report.unknown_ids.join(", ")}`);
  }
  console.log("\nFamily coverage:");
  for (const family of listFamilies()) {
    const count = report.coverage.families[family.slug] || 0;
    const mark = count > 0 ? "x" : " ";
    console.log(`  [${mark}] ${family.name} (${count})`);
  }
  if (Object.keys(report.coverage.stack_levels).length > 0) {
    console.log("\nStack levels: " + Object.keys(report.coverage.stack_levels).join(", "));
  }
  if (report.recommendations.length > 0) {
    console.log("\nUncovered families (one example entry each, not a ranked pick):");
    for (const rec of report.recommendations) {
      const family = getFamily(rec.family);
      console.log(`  + ${family ? family.name : rec.family}: e.g. ${rec.title} (${rec.id})`);
      if (rec.alternatives.length > 0) {
        console.log(`      or any of: ${rec.alternatives.map((a) => `${a.title} (${a.id})`).join(", ")}`);
      }
    }
    console.log(`\nCoverage rule: ${report.composition_rule.description}`);
  }
}

function main() {
  const { flags, command, args } = resolveInvocation(process.argv.slice(2));

  switch (command) {
    case "help": {
      process.stdout.write(USAGE);
      break;
    }
    case "list": {
      if (flags.family && !getFamily(flags.family)) {
        const guess = nearest(flags.family, listFamilies().map((f) => f.slug));
        fail(flags.json, { error: "unknown family", family: flags.family, did_you_mean: guess || undefined },
          `Unknown family '${flags.family}'.${hint(guess)} Run 'families' to see valid slugs.`);
      }
      const sensors = listSensors({ family: flags.family });
      emit(flags, sensors.map(sensorSummary), () => humanList(sensors));
      break;
    }
    case "families": {
      emit(flags, listFamilies(), humanFamilies);
      break;
    }
    case "get": {
      const query = args.join(" ");
      const sensor = findSensor(query);
      if (!sensor) {
        fail(flags.json, { error: "no match", query }, `No sensor matches '${query}'.`);
      }
      const related = getRelated(sensor);
      emit(
        flags,
        { ...sensorSummary(sensor), frontmatter: sensor.frontmatter, body_text: sensor.body_text, body_html: sensor.body_html, related },
        () => humanGet(sensor, related)
      );
      break;
    }
    case "search": {
      const needle = args.join(" ").toLowerCase();
      const matches = searchSensors(args)
        .map((s) => ({ sensor: s, score: scoreSearch(s, needle) }))
        .sort((a, b) => b.score - a.score || a.sensor.slug.localeCompare(b.sensor.slug));
      emit(
        flags,
        matches.map(({ sensor, score }) => ({ ...sensorSummary(sensor), score, snippet: snippet(sensor, needle) })),
        () => {
          for (const { sensor } of matches) {
            console.log(`${sensor.id.padEnd(9)} ${sensor.title} (${sensor.slug})`);
            console.log(`           ${snippet(sensor, needle)}`);
          }
          console.log(`\n${matches.length} match(es)`);
        }
      );
      break;
    }
    case "values": {
      // An unknown field used to return an empty list and exit 0, which is
      // indistinguishable from a field that genuinely has no values.
      const field = args[0];
      const fields = listFields();
      if (!fields.includes(field)) {
        const guess = nearest(field, fields);
        fail(flags.json, { error: "unknown field", field, did_you_mean: guess || undefined, valid_fields: fields },
          `Unknown field '${field}'.${hint(guess)} Valid fields: ${fields.join(", ")}.`);
      }
      const values = listValues(field);
      emit(flags, { field, values }, () => values.forEach((v) => console.log(v)));
      break;
    }
    case "suggest":
    case "gaps": {
      const results = suggestSensors(args.join(" "));
      const gapsOnly = command === "gaps";
      emit(
        flags,
        gapsOnly ? results.filter((r) => r.gap) : results,
        () => humanSuggest(results, { gapsOnly })
      );
      break;
    }
    case "stack": {
      const ids = args.join(" ").split(/[,\s]+/).filter(Boolean);
      if (ids.length === 0) {
        fail(flags.json, { error: "missing argument", command, usage: "softwareobservatory stack <id,slug,...>" },
          "Usage: softwareobservatory stack <id,slug,...>");
      }
      const report = stackCoverage(ids);
      emit(flags, report, () => humanStack(report));
      break;
    }
    case "mcp": {
      startMcpServer();
      break;
    }
    case "version": {
      const data = loadData();
      emit(
        flags,
        { cli: CLI_VERSION, dataset_version: data.version, dataset_generated_at: data.generated_at, sensors: data.sensors.length },
        () => {
          console.log(`softwareobservatory ${CLI_VERSION}`);
          console.log(`dataset v${data.version}, generated ${data.generated_at}, ${data.sensors.length} sensors`);
        }
      );
      break;
    }
    /* c8 ignore next 3 */
    default:
      // resolveInvocation rejects anything not in COMMANDS, so this is
      // unreachable unless COMMANDS and this switch drift apart.
      fail(flags.json, { error: "unimplemented command", command }, `Command '${command}' is declared but not implemented.`);
  }
}

main();
