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
  return execFileSync("node", [BIN, ...args], { encoding: "utf8", input, stdio: ["pipe", "pipe", "pipe"] });
}

// Run a command that must fail. Returns { status, stdout, stderr }.
function runFail(args) {
  try {
    run(args);
  } catch (error) {
    if (typeof error.status !== "number") throw error;
    return { status: error.status, stdout: error.stdout || "", stderr: error.stderr || "" };
  }
  throw new Error(`expected '${args.join(" ")}' to exit non-zero`);
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
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
  const { status, stderr } = runFail(["frobnicate"]);
  assert(status === 1, `expected exit 1, got ${status}`);
  assert(stderr.includes("frobnicate"), "error should name the unknown command");
});

// --- argument validation (issue #120) ---------------------------------------
// The bug: `list --familly structural` returned all 59 sensors and exited 0.
// Nothing may be silently discarded; every case below must exit 1.

check("unknown flag exits nonzero and names the flag", () => {
  const { status, stdout, stderr } = runFail(["list", "--familly", "structural"]);
  assert(status === 1, `expected exit 1, got ${status}`);
  assert(stdout === "", "nothing may be written to stdout on failure");
  const payload = JSON.parse(stderr);
  assert(payload.error === "unknown flag", `expected error 'unknown flag', got ${payload.error}`);
  assert(payload.flag === "--familly", `expected flag '--familly', got ${payload.flag}`);
  assert(payload.did_you_mean === "--family", "expected a did_you_mean suggestion");
});

check("unknown flag is rejected for every command", () => {
  for (const args of [["families", "--nope"], ["get", "linter", "--nope"], ["version", "--nope"],
                      ["search", "mutation", "--nope"], ["values", "oracle", "--nope"],
                      ["suggest", "flaky", "--nope"], ["gaps", "flaky", "--nope"], ["stack", "linter", "--nope"]]) {
    const { status, stderr } = runFail(args);
    assert(status === 1, `${args.join(" ")}: expected exit 1, got ${status}`);
    assert(JSON.parse(stderr).flag === "--nope", `${args.join(" ")}: error should name --nope`);
  }
});

check("--family with no value exits nonzero", () => {
  const { status, stderr } = runFail(["list", "--family"]);
  assert(status === 1, `expected exit 1, got ${status}`);
  assert(JSON.parse(stderr).error === "missing flag value", "expected a missing-value error");
});

check("--family is rejected on commands that do not take it", () => {
  const { status, stderr } = runFail(["get", "--family", "structural", "linter"]);
  assert(status === 1, `expected exit 1, got ${status}`);
  assert(JSON.parse(stderr).error === "flag not valid for command", "expected a flag-not-valid error");
});

check("stray positional exits nonzero and suggests the flag", () => {
  const { status, stderr } = runFail(["list", "structural"]);
  assert(status === 1, `expected exit 1, got ${status}`);
  const payload = JSON.parse(stderr);
  assert(payload.error === "unexpected argument", `expected 'unexpected argument', got ${payload.error}`);
  assert(payload.did_you_mean === "--family structural", "expected a --family suggestion");
});

check("missing required arguments exit nonzero", () => {
  for (const args of [["get"], ["search"], ["values"], ["suggest"], ["gaps"], ["stack"]]) {
    const { status, stderr } = runFail(args);
    assert(status === 1, `${args[0]}: expected exit 1, got ${status}`);
    assert(JSON.parse(stderr).error === "missing argument", `${args[0]}: expected a missing-argument error`);
  }
});

check("values rejects an unknown field instead of returning nothing", () => {
  const { status, stderr } = runFail(["values", "bogusfield"]);
  assert(status === 1, `expected exit 1, got ${status}`);
  const payload = JSON.parse(stderr);
  assert(payload.error === "unknown field", `expected 'unknown field', got ${payload.error}`);
  assert(payload.valid_fields.includes("oracle"), "expected the valid field list in the error");
});

check("unknown family still errors with a suggestion", () => {
  const { status, stderr } = runFail(["list", "--family", "structual"]);
  assert(status === 1, `expected exit 1, got ${status}`);
  const payload = JSON.parse(stderr);
  assert(payload.error === "unknown family", `expected 'unknown family', got ${payload.error}`);
  assert(payload.did_you_mean === "structural", "expected a did_you_mean suggestion");
});

check("--json and --plain together is an error, not a silent coercion", () => {
  assert(runFail(["list", "--json", "--plain"]).status === 1, "expected exit 1");
});

check("a repeated flag is an error, not last-one-wins", () => {
  assert(runFail(["list", "--family", "structural", "--family", "runtime"]).status === 1, "expected exit 1");
});

check("--family=value form works", () => {
  const out = runJson(["list", "--family=structural"]);
  assert(out.length > 0 && out.every((s) => s.family === "structural"), "family filter broken");
});

check("help is a command, not an unknown one", () => {
  const out = run(["help"]);
  assert(out.includes("Usage: softwareobservatory"), "help should print usage");
  for (const flag of ["--help", "-h"]) {
    assert(run([flag]).includes("Usage: softwareobservatory"), `${flag} should print usage`);
  }
});

// --- suggest ranking (issue #121) -------------------------------------------
// The bug: the README's own headline example returned Contract Tests and
// Example-Based Tests, because "tests" and "pass" substring-matched.

check("README example: 'our tests pass but bugs still ship'", () => {
  const out = runJson(["suggest", "our tests pass but bugs still ship"]);
  const slugs = out.map((r) => r.slug);
  assert(slugs[0] === "mutation-testing", `expected mutation-testing first, got ${slugs.join(", ")}`);
  assert(slugs.includes("escaped-defect-rate"), `expected escaped-defect-rate in results, got ${slugs.join(", ")}`);
  assert(out.every((r) => r.basis === "keyword"), "every result should declare how it was produced");
});

check("README example: gaps for AI-generated code", () => {
  const out = runJson(["gaps", "how do I know my ai-generated code is safe"]);
  const slugs = out.map((r) => r.slug);
  assert(slugs.includes("second-agent-review"), `expected second-agent-review, got ${slugs.join(", ")}`);
});

check("suggest matches on word starts, not substrings", () => {
  // 'ai' used to match the 'ai' inside 'Time-to-Repair'.
  const out = runJson(["suggest", "reviewing ai output"]);
  assert(!out.some((r) => r.slug === "time-to-repair"), "'ai' should not match inside 'Time-to-Repair'");
  // A question made only of stopwords has no signal and must return nothing.
  assert(runJson(["suggest", "we are just going to do the thing"]).length === 0, "stopword-only question should return no suggestions");
});

check("suggest survives every documented example query", () => {
  for (const question of [
    "our tests pass but bugs still ship",
    "I need to review AI-generated code",
    "we keep shipping regressions",
    "we're starting a greenfield service",
    "our deploys keep breaking production",
  ]) {
    const out = runJson(["suggest", question]);
    assert(out.length > 0, `no suggestions for '${question}'`);
    assert(out.every((r) => typeof r.score === "number" && r.id && r.slug), `malformed result for '${question}'`);
  }
});

// --- README command coverage -------------------------------------------------

check("every command shown in the READMEs runs clean", () => {
  const documented = [
    ["list", "--family", "structural"],
    ["get", "SO-003"],
    ["search", "mutation"],
    ["suggest", "our tests pass but bugs still ship"],
    ["gaps", "how do I know my ai-generated code is safe"],
    ["stack", "linter,SO-003,canary-analysis"],
    ["values", "oracle"],
    ["families"],
    ["version"],
  ];
  for (const args of documented) {
    const out = runJson(args);
    assert(out !== null && out !== undefined, `${args.join(" ")} produced nothing`);
    if (Array.isArray(out)) assert(out.length > 0, `${args.join(" ")} produced an empty array`);
  }
});

check("stack does not present its arbitrary pick as a ranked recommendation", () => {
  const out = runJson(["stack", "linter,SO-003"]);
  assert(out.composition_rule?.id === "one-per-family", "expected the composition rule to be stated");
  for (const rec of out.recommendations) {
    assert(rec.basis === "family-coverage", "recommendation should declare its basis");
    assert(Array.isArray(rec.alternatives), "recommendation should list the family's other entries");
    assert(/example entry point/.test(rec.reason), "reason should not claim the pick is ranked");
  }
});

if (failures > 0) {
  console.error(`\n${failures} failure(s)`);
  process.exit(1);
}
console.log("\nAll smoke tests passed.");
