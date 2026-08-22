import { readFile, readdir } from "node:fs/promises";
import path from "node:path";

const repoRoot = path.resolve(import.meta.dirname, "..");
const compoundersRoot = path.join(repoRoot, "compounders");

const tickerEntries = await readdir(compoundersRoot, { withFileTypes: true });
const profileFiles = tickerEntries
  .filter((entry) => entry.isDirectory() && /^\d{4}$/.test(entry.name))
  .map((entry) => path.join(compoundersRoot, entry.name, "initiation", "index.html"));

const libraryFiles = [
  path.join(compoundersRoot, "index.html"),
  path.join(compoundersRoot, "profiles", "index.html"),
];

const bannedPhrases = [
  ["経営陣", "attribute the fact to the company, board, disclosure, briefing, or a named executive"],
  ["経営者", "name the executive or describe the company, board, or management structure precisely"],
  ["経営者の負担", "use a neutral label such as 実行負担"],
  ["経営側のコスト", "use a neutral label such as 実行負担"],
  ["経営側コスト", "use a neutral label such as 実行負担"],
  ["経営コスト", "use a neutral label such as 実行負担"],
  ["経営の負担", "use a neutral label such as 実行負担"],
  ["打ち手", "frame the item as an observable question, change, policy, or valuation condition"],
  ["資本効率レバー", "frame the section as neutral valuation factors"],
  ["3つのレバー", "frame the items as neutral valuation factors"],
  ["会社ができることを三つ挙げる", "describe the three factors that could change the valuation"],
  ["株主に返すのか", "frame the issue as a capital-allocation or valuation condition"],
  ["死蔵させるのか", "describe the cash position without imputing hostile intent"],
  ["膿を出した", "name the restructuring action directly"],
  ["株主を後回し", "describe the disclosed allocation between investment, debt reduction, and returns"],
  ["会社に要求する", "state the disclosure or listing requirement neutrally"],
  ["還元を先送り", "describe the timing or current policy without accusing the issuer"],
  ["アクティビストの圧力", "attribute the proposal or holding to the activist without adopting its stance"],
  ["会社側に必要なのは", "describe the information gap or evaluation condition neutrally"],
  ["会社側のコスト", "use a neutral label such as 実行負担"],
  ["これを直すには", "describe the factors that would restore confidence without issuing instructions"],
  ["加えるだけでよい", "describe the additional information and its analytical value neutrally"],
  ["説明した方がよい", "describe the information as an evaluation factor rather than advice to the issuer"],
  ["明文化するだけ", "describe the policy condition without prescribing issuer action"],
];

const failures = [];

for (const file of [...profileFiles, ...libraryFiles]) {
  let source;
  try {
    source = await readFile(file, "utf8");
  } catch (error) {
    if (error?.code === "ENOENT") continue;
    throw error;
  }

  const relativeFile = path.relative(repoRoot, file).replaceAll(path.sep, "/");
  const lines = source.split(/\r?\n/);

  for (const [phrase, guidance] of bannedPhrases) {
    lines.forEach((line, index) => {
      if (line.includes(phrase)) {
        failures.push(`${relativeFile}:${index + 1}: ${phrase} — ${guidance}`);
      }
    });
  }
}

if (failures.length > 0) {
  console.error("Japanese Compounder issuer-posture check failed:\n");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(
  `Japanese Compounder issuer-posture check passed: ${profileFiles.length} profiles and ${libraryFiles.length} library pages.`,
);
