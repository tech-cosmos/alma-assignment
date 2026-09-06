// Fetch the live OpenAPI document from the running FastAPI service and overwrite
// ./openapi.json. Run `npm run openapi:pull` (which also regenerates the TS types).
import { writeFile } from "node:fs/promises";

const base = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/+$/, "");
const url = `${base}/openapi.json`;

try {
  const res = await fetch(url);
  if (!res.ok) {
    console.error(`GET ${url} -> ${res.status} ${res.statusText}`);
    process.exit(1);
  }
  const spec = await res.json();
  await writeFile(new URL("../openapi.json", import.meta.url), JSON.stringify(spec, null, 2) + "\n");
  console.log(`Wrote openapi.json from ${url} (${spec.info?.title ?? "untitled"} ${spec.info?.version ?? ""})`);
} catch (err) {
  console.error(`Could not fetch ${url}: ${err instanceof Error ? err.message : err}`);
  console.error("Is the backend running? Set NEXT_PUBLIC_API_URL to override the base URL.");
  process.exit(1);
}
