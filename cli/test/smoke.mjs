// Smoke test: exercises every command in JSON mode plus the MCP handshake.
// Run with: node cli/test/smoke.mjs
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const BIN = fileURLToPath(new URL("../bin/softwareobservatory.mjs", import.meta.url));

let failures = 0;

function check(name, fn) {
  try {
    fn();
    console.log(`ok - ${name}`);
  } catch (error) {
    failures += 1;
    console.error(`FAIL - ${name}: ${error.message}`);
  }
}

function run(args, { input } = {}) {
  return execFileSync("node", [BIN, ...args], { encoding: "utf8", input });
}

function runJson(args) {
  return JSON.parse(run(args));
}

check("list returns all sensors as JSON", () => {
  const out = runJson(["list"]);
  if (!Array.isArray(out) || out.length < 50) throw new Error(`expected 50+ sensors, got ${out.length}`);
});

check("list --family filters", () => {
  const out = runJson(["list", "--family", "structural"]);
  if (out.length === 0 || out.some((s) => s.family !== "structural")) throw new Error("family filter broken");
});

check("get resolves id, slug, and title", () => {
  for (const query of ["SO-001c", "linter", "Linter"]) {
    const out = runJson(["get", query]);
    if (out.slug !== "linter") throw new Error(`'${query}' resolved to ${out.slug}`);
  }
  if (!runJson(["get", "linter"]).related.length) throw new Error("expected related entries");
});

check("search finds mutation testing", () => {
  const out = runJson(["search", "mutation"]);
  if (!out.some((m) => m.slug === "mutation-testing")) throw new Error("mutation-testing not in results");
});

check("suggest ranks and marks gaps", () => {
  const out = runJson(["suggest", "would our tests catch a wrong implementation"]);
  if (out.length === 0) throw new Error("no suggestions");
  if (!out[0].id) throw new Error("missing id field");
  if (!out.some((r) => r.gap)) throw new Error("expected at least one gap marker");
});

check("gaps returns only family-first results", () => {
  const out = runJson(["gaps", "would our tests catch a wrong implementation"]);
  if (out.some((r) => !r.gap)) throw new Error("non-gap result in gaps output");
});

check("stack reports coverage and recommendations", () => {
  const out = runJson(["stack", "linter,SO-003"]);
  if (out.selected.length !== 2) throw new Error("expected 2 selected");
  if (!out.missing_families.length) throw new Error("expected missing families");
  if (!out.recommendations.length) throw new Error("expected recommendations");
});

check("values lists distinct frontmatter values", () => {
  const out = runJson(["values", "oracle"]);
  if (!out.values.includes("maximum")) throw new Error("expected 'maximum' in oracle values");
});

check("mcp handshake, tools/list, and tools/call", () => {
  const transcript = [
    { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "smoke", version: "0" } } },
    { jsonrpc: "2.0", method: "notifications/initialized" },
    { jsonrpc: "2.0", id: 2, method: "tools/list" },
    { jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "get_sensor", arguments: { query: "fuzzing" } } },
    { jsonrpc: "2.0", id: 4, method: "resources/read", params: { uri: "softwareobservatory://families" } },
  ];
  const out = run(["mcp"], { input: transcript.map((m) => JSON.stringify(m)).join("\n") + "\n" });
  const replies = out.trim().split("\n").map((line) => JSON.parse(line));
  const byId = new Map(replies.map((r) => [r.id, r]));
  if (byId.get(1)?.result?.serverInfo?.name !== "softwareobservatory") throw new Error("initialize failed");
  const tools = byId.get(2)?.result?.tools?.map((t) => t.name) || [];
  for (const expected of ["list_families", "list_sensors", "get_sensor", "suggest_sensors", "stack_coverage"]) {
    if (!tools.includes(expected)) throw new Error(`missing tool ${expected}`);
  }
  const sensor = JSON.parse(byId.get(3).result.content[0].text);
  if (sensor.slug !== "fuzzing") throw new Error("get_sensor returned wrong sensor");
  const families = JSON.parse(byId.get(4).result.contents[0].text);
  if (!Array.isArray(families) || families.length !== 10) throw new Error("families resource broken");
});

check("unknown command exits nonzero", () => {
  try {
    run(["frobnicate"]);
    throw new Error("expected nonzero exit");
  } catch (error) {
    if (error.status !== 1) throw error;
  }
});

if (failures > 0) {
  console.error(`\n${failures} failure(s)`);
  process.exit(1);
}
console.log("\nAll smoke tests passed.");
