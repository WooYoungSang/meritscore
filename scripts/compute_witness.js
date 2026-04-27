#!/usr/bin/env node
/**
 * Compute witness binary from input JSON using the circuit WASM directly.
 * Bypasses `snarkjs wtns calculate` which has a CLI-only constraint-check bug.
 *
 * Usage: node scripts/compute_witness.js <input.json> <output.wtns>
 */

const { readFileSync, writeFileSync } = require("fs");
const path = require("path");

const [, , inputPath, outputPath] = process.argv;
if (!inputPath || !outputPath) {
  console.error("Usage: node compute_witness.js <input.json> <output.wtns>");
  process.exit(1);
}

const wc = require(path.resolve(__dirname, "../circuits/merit_threshold_js/witness_calculator.js"));
const wasmBuffer = readFileSync(
  path.resolve(__dirname, "../circuits/merit_threshold_js/merit_threshold.wasm")
);
const input = JSON.parse(readFileSync(inputPath, "utf8"));

wc(wasmBuffer).then(async (calc) => {
  const wtns = await calc.calculateWTNSBin(input, 1); // 1 = check constraints
  writeFileSync(outputPath, wtns);
  console.log("OK");
}).catch((e) => {
  console.error("ERROR:", e.message);
  process.exit(1);
});
