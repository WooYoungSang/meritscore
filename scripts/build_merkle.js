#!/usr/bin/env node
/**
 * Builds a depth-8 Merkle tree using real circomlib Poseidon hash.
 * Outputs JSON: { root, agents: { alice: {leaf, path, indices}, bob: ..., carol: ... } }
 *
 * Usage: node scripts/build_merkle.js
 */

const { buildPoseidon } = require("circomlibjs");

const DEPTH = 8;
const TREE_SIZE = 1 << DEPTH; // 256

// Agents: sorted by name (alice=0, bob=1, carol=2)
const AGENTS = [
  { name: "alice", addr: 1n, score: 2641n, idx: 0 },
  { name: "bob",   addr: 2n, score: 6703n, idx: 1 },
  { name: "carol", addr: 3n, score: 0n,    idx: 2 },
];

async function main() {
  const poseidon = await buildPoseidon();
  const F = poseidon.F;

  const toBI = (v) => BigInt(F.toObject(v).toString());

  const poseidon2 = (a, b) => toBI(poseidon([a, b]));

  // Build depth-8 tree: 256 leaves, agents at 0..2, rest = 0
  const leaves = new Array(TREE_SIZE).fill(0n);
  for (const agent of AGENTS) {
    leaves[agent.idx] = poseidon2(agent.addr, agent.score);
  }

  // Build tree level by level
  const levels = [leaves.slice()];
  let current = leaves.slice();
  for (let d = 0; d < DEPTH; d++) {
    const next = [];
    for (let i = 0; i < current.length; i += 2) {
      next.push(poseidon2(current[i], current[i + 1]));
    }
    levels.push(next);
    current = next;
  }

  const root = levels[DEPTH][0];

  // Generate proof for each agent
  const result = { root: root.toString(), agents: {} };

  for (const agent of AGENTS) {
    const leaf = leaves[agent.idx];
    const path = [];
    const indices = [];
    let pos = agent.idx;

    for (let d = 0; d < DEPTH; d++) {
      const isRight = pos % 2 === 1;
      const siblingPos = isRight ? pos - 1 : pos + 1;
      indices.push(isRight ? 1 : 0);
      path.push(levels[d][siblingPos].toString());
      pos = Math.floor(pos / 2);
    }

    result.agents[agent.name] = {
      leaf: leaf.toString(),
      addr: agent.addr.toString(),
      score: agent.score.toString(),
      merklePath: path,
      pathIndices: indices,
    };
  }

  console.log(JSON.stringify(result));
}

main().catch((e) => { console.error(e); process.exit(1); });
