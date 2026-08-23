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
  suggestSensors,
  stackCoverage,
} from "../lib/core.mjs";
import { startMcpServer } from "../lib/mcp.mjs";

const USAGE = `softwareobservatory - query the Software Observatory sensor catalog

Usage: softwareobservatory [--json] [--plain] <command> [args]

Commands:
  list [--family <slug>]        List sensors (all, or within one family)
  families                      List the 11 sensor families
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
  --json   Machine-readable output (full precision; stable for agents)
  --plain  Force human-readable output (default when stdout is a TTY)
`;

function parseFlags(argv) {
  const flags = { json: false, plain: false, family: null };
  const rest = [];
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--json") flags.json = true;
    else if (arg === "--plain") flags.plain = true;
    else if (arg === "--family") {
      flags.family = argv[i + 1];
      i += 1;
    } else if (arg === "--help" || arg === "-h") {
      flags.help = true;
    } else {
      rest.push(arg);
    }
  }
  if (!process.stdout.isTTY) flags.json = true;
  if (flags.plain) flags.json = false;
  return { flags, rest };
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
    (s) => s.title.toLowerCase().includes(needle) || s.body_text.includes(needle)
  );
}

function scoreSearch(sensor, needle) {
  let score = 0;
  if (sensor.title.toLowerCase().includes(needle)) score += 10;
  const occurrences = sensor.body_text.split(needle).length - 1;
  return score + Math.min(occurrences, 5);
}

function snippet(sensor, needle) {
  const index = sensor.body_text.indexOf(needle);
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
    console.log("\nRecommendations:");
    for (const rec of report.recommendations) {
      console.log(`  + ${rec.title} (${rec.id}) - ${rec.reason}`);
    }
  }
}

function main() {
  const { flags, rest } = parseFlags(process.argv.slice(2));
  const [command, ...args] = rest;

  if (flags.help || !command) {
    process.stdout.write(USAGE);
    process.exit(command ? 0 : 1);
  }

  switch (command) {
    case "list": {
      if (flags.family && !getFamily(flags.family)) {
        console.error(`Unknown family '${flags.family}'. Run 'families' to see valid slugs.`);
        process.exit(1);
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
      if (args.length === 0) {
        console.error("Usage: softwareobservatory get <id|slug|title>");
        process.exit(1);
      }
      const sensor = findSensor(args.join(" "));
      if (!sensor) {
        console.error(`No sensor matches '${args.join(" ")}'.`);
        process.exit(1);
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
      if (args.length === 0) {
        console.error("Usage: softwareobservatory values <field>");
        process.exit(1);
      }
      const values = listValues(args[0]);
      emit(flags, { field: args[0], values }, () => values.forEach((v) => console.log(v)));
      break;
    }
    case "suggest":
    case "gaps": {
      if (args.length === 0) {
        console.error(`Usage: softwareobservatory ${command} <question...>`);
        process.exit(1);
      }
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
      if (args.length === 0) {
        console.error("Usage: softwareobservatory stack <id,slug,...>");
        process.exit(1);
      }
      const ids = args.join(" ").split(/[,\s]+/).filter(Boolean);
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
    default:
      console.error(`Unknown command '${command}'.\n`);
      process.stdout.write(USAGE);
      process.exit(1);
  }
}

main();
