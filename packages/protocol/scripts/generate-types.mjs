// 从 schemas/ 的 JSON Schema 生成 TS 类型（契约先行：schema 是事实源，类型是派生物）。
// 生成的类型入库供各包引用，构建期可重生成。不手写、不与 schema 漂移。
import { compile } from "json-schema-to-typescript";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../../..");
const schemasDir = path.join(repoRoot, "schemas");
const outDir = path.join(here, "../src/generated");

const SCHEMAS = [
  ["phenomenon.v1.schema.json", "PhenomenonV1"],
  ["save.v1.schema.json", "SaveV1"],
  ["timeline.v1.schema.json", "TimelineV1"],
  ["compound.v1.schema.json", "CompoundV1"],
  ["apparatus.v1.schema.json", "ApparatusV1"],
  ["reaction_rule.v1.schema.json", "ReactionRuleV1"],
  ["solution_speciation.v1.schema.json", "SolutionSpeciationV1"],
];

await mkdir(outDir, { recursive: true });

for (const [file, declareName] of SCHEMAS) {
  const schemaPath = path.join(schemasDir, file);
  const schema = JSON.parse(await readFile(schemaPath, "utf8"));
  const ts = await compile(schema, declareName, {
    bannerComment: `// GENERATED from schemas/${file} — DO NOT EDIT. Run pnpm build:types.`,
    additionalProperties: false,
    format: true,
  });
  const outName = file.replace(/\.schema\.json$/, ".d.ts");
  await writeFile(path.join(outDir, outName), ts, "utf8");
  console.log(`generated: ${outName}`);
}
