// polyglot CLI: prints a JSON summary of the report to stdout.
import { readFileSync } from "node:fs";

const path = process.argv[2] ?? "report.json";
console.log("reading", path);
const rows = JSON.parse(readFileSync(path, "utf8"));
process.stdout.write(JSON.stringify({ count: rows.length }) + "\n");
