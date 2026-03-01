import { spawn } from "node:child_process";
import process from "node:process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const nextBin = path.resolve(__dirname, "../node_modules/.bin/next");

const child = spawn(nextBin, ["dev", "--hostname", "127.0.0.1"], {
  stdio: ["inherit", "pipe", "pipe"],
  env: process.env,
});

let warming = false;
let warmed = false;
let baseUrl = "http://127.0.0.1:3000";

child.stdout.on("data", (chunk) => {
  const text = chunk.toString();
  process.stdout.write(text);
  const localUrlMatch = text.match(/Local:\s+(http:\/\/localhost:\d+)/);
  if (localUrlMatch) {
    baseUrl = localUrlMatch[1].replace("http://localhost", "http://127.0.0.1");
  }
  if (!warming && !warmed && text.includes("Ready")) {
    warming = true;
    void warmupRoutes().finally(() => {
      warming = false;
      warmed = true;
    });
  }
});

child.stderr.on("data", (chunk) => {
  process.stderr.write(chunk.toString());
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});

for (const event of ["SIGINT", "SIGTERM"]) {
  process.on(event, () => child.kill(event));
}

async function warmupRoutes() {
  const routes = [
    "/overview",
    "/analytics",
    "/cost-explorer",
    "/trends",
    "/budgets",
    "/ai",
    "/settings",
    "/dashboard/weekly",
  ];
  for (const route of routes) {
    const ok = await waitUntilOk(route, 20);
    process.stdout.write(`[dev-warmup] ${route} ${ok ? "ready" : "failed"}\n`);
  }
}

async function waitUntilOk(route, maxAttempts) {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    try {
      const response = await fetch(`${baseUrl}${route}`, {
        method: "HEAD",
        redirect: "manual",
      });
      if (response.ok) {
        return true;
      }
    } catch {
      // Server may still be starting or compiling lazily.
    }
    await sleep(400);
  }
  return false;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
