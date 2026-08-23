import readline from "node:readline";
import {
  CLI_VERSION,
  loadData,
  siteUrl,
  listFamilies,
  getFamily,
  listSensors,
  findSensor,
  getRelated,
  suggestSensors,
  stackCoverage,
} from "./core.mjs";

const PROTOCOL_VERSION = "2024-11-05";
const SERVER_INFO = { name: "softwareobservatory", version: CLI_VERSION };

const TOOLS = [
  {
    name: "list_families",
    description: "List the 11 sensor families of the Software Observatory catalog.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "list_sensors",
    description: "List sensors, optionally filtered by family slug.",
    inputSchema: {
      type: "object",
      properties: {
        family: { type: "string", description: "Family slug, e.g. 'structural' or 'adversarial'." },
      },
    },
  },
  {
    name: "get_sensor",
    description: "Get one sensor by id (SO-###), slug, or exact title, including its full entry text and related sensors.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Sensor id, slug, or exact title." },
      },
      required: ["query"],
    },
  },
  {
    name: "suggest_sensors",
    description:
      "Given a plain-language description of a project or concern, suggest sensors whose entries address it. Results flagged 'gap' are the first suggestion from a family not yet represented by a higher-scoring result.",
    inputSchema: {
      type: "object",
      properties: {
        question: { type: "string", description: "The concern to match, e.g. 'our tests pass but bugs still ship'." },
        limit: { type: "number", description: "Max results (default 5)." },
      },
      required: ["question"],
    },
  },
  {
    name: "stack_coverage",
    description:
      "Assess a set of sensors (by id or slug) for family and confidence-stack coverage, and recommend sensors for uncovered families.",
    inputSchema: {
      type: "object",
      properties: {
        ids: { type: "array", items: { type: "string" }, description: "Sensor ids or slugs." },
      },
      required: ["ids"],
    },
  },
];

function sensorSummary(sensor) {
  return {
    id: sensor.id,
    slug: sensor.slug,
    title: sensor.title,
    family: sensor.family,
    url: siteUrl(sensor.url_path),
  };
}

function callTool(name, args = {}) {
  switch (name) {
    case "list_families":
      return listFamilies();
    case "list_sensors":
      return listSensors({ family: args.family }).map((s) => ({
        ...sensorSummary(s),
        oracle: s.frontmatter.oracle,
        latency: s.frontmatter.latency,
        type: s.frontmatter.type,
      }));
    case "get_sensor": {
      const sensor = findSensor(args.query || "");
      if (!sensor) return { error: `no sensor matches '${args.query}'` };
      return { ...sensorSummary(sensor), frontmatter: sensor.frontmatter, body_text: sensor.body_text, related: getRelated(sensor) };
    }
    case "suggest_sensors":
      return suggestSensors(args.question || "", { limit: args.limit });
    case "stack_coverage":
      return stackCoverage(args.ids || []);
    default:
      throw Object.assign(new Error(`unknown tool '${name}'`), { code: -32602 });
  }
}

function resources() {
  return [
    { uri: "softwareobservatory://families", name: "Sensor families", mimeType: "application/json" },
    ...loadData().sensors.map((s) => ({
      uri: `softwareobservatory://sensor/${s.slug}`,
      name: s.title,
      description: `${s.id} (${s.family})`,
      mimeType: "application/json",
    })),
  ];
}

function readResource(uri) {
  const data = loadData();
  if (uri === "softwareobservatory://families") {
    return JSON.stringify(data.families, null, 2);
  }
  const match = uri.match(/^softwareobservatory:\/\/sensor\/(.+)$/);
  if (match) {
    const sensor = findSensor(match[1]);
    if (sensor) return JSON.stringify({ ...sensor, url: siteUrl(sensor.url_path) }, null, 2);
  }
  throw Object.assign(new Error(`unknown resource '${uri}'`), { code: -32602 });
}

function respond(id, result, error) {
  const message = { jsonrpc: "2.0", id };
  if (error) message.error = { code: error.code || -32603, message: error.message };
  else message.result = result;
  process.stdout.write(JSON.stringify(message) + "\n");
}

function handleMessage(message) {
  const { id, method, params = {} } = message;
  try {
    switch (method) {
      case "initialize":
        respond(id, { protocolVersion: PROTOCOL_VERSION, capabilities: { tools: {}, resources: {} }, serverInfo: SERVER_INFO });
        break;
      case "ping":
        respond(id, {});
        break;
      case "notifications/initialized":
        break;
      case "tools/list":
        respond(id, { tools: TOOLS });
        break;
      case "tools/call": {
        const result = callTool(params.name, params.arguments);
        respond(id, { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] });
        break;
      }
      case "resources/list":
        respond(id, { resources: resources() });
        break;
      case "resources/read": {
        const text = readResource(params.uri);
        respond(id, { contents: [{ uri: params.uri, mimeType: "application/json", text }] });
        break;
      }
      default:
        if (id !== undefined && id !== null) {
          respond(id, null, { code: -32601, message: `method not found: ${method}` });
        }
    }
  } catch (error) {
    respond(id ?? null, null, { code: error.code || -32603, message: error.message });
  }
}

export function startMcpServer() {
  const rl = readline.createInterface({ input: process.stdin });
  rl.on("line", (line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    let message;
    try {
      message = JSON.parse(trimmed);
    } catch {
      respond(null, null, { code: -32700, message: "parse error" });
      return;
    }
    handleMessage(message);
  });
}
