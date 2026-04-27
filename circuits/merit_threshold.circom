pragma circom 2.0.0;
include "circomlib/circuits/poseidon.circom";
include "circomlib/circuits/comparators.circom";
include "circomlib/circuits/mux1.circom";

// Merkle tree proof circuit for merit scores
// Proves:
// 1. agentAddr + agentScore hashes to a leaf
// 2. leaf is in merkle tree (given root)
// 3. agentScore >= threshold

template MeritThreshold() {
    // Private inputs
    signal input agentAddr;
    signal input agentScore;
    signal input merklePath[8];    // 8 sibling hashes for depth-8 tree
    signal input pathIndices[8];   // 0 or 1: which side is this node

    // Public inputs
    signal input merkleRoot;
    signal input threshold;

    // Step 1: Hash the agent's data to create a leaf
    component leafHash = Poseidon(2);
    leafHash.inputs[0] <== agentAddr;
    leafHash.inputs[1] <== agentScore;
    signal leaf <== leafHash.out;

    // Step 2: Verify merkle proof by computing root
    // For each level, use Mux1 to select left/right order

    // Level 0
    component level0Hash = Poseidon(2);
    component mux0Left = Mux1();
    mux0Left.c[0] <== leaf;
    mux0Left.c[1] <== merklePath[0];
    mux0Left.s <== pathIndices[0];
    signal node0Left <== mux0Left.out;

    component mux0Right = Mux1();
    mux0Right.c[0] <== merklePath[0];
    mux0Right.c[1] <== leaf;
    mux0Right.s <== pathIndices[0];
    signal node0Right <== mux0Right.out;

    level0Hash.inputs[0] <== node0Left;
    level0Hash.inputs[1] <== node0Right;
    signal level0 <== level0Hash.out;

    // Level 1
    component level1Hash = Poseidon(2);
    component mux1Left = Mux1();
    mux1Left.c[0] <== level0;
    mux1Left.c[1] <== merklePath[1];
    mux1Left.s <== pathIndices[1];
    signal node1Left <== mux1Left.out;

    component mux1Right = Mux1();
    mux1Right.c[0] <== merklePath[1];
    mux1Right.c[1] <== level0;
    mux1Right.s <== pathIndices[1];
    signal node1Right <== mux1Right.out;

    level1Hash.inputs[0] <== node1Left;
    level1Hash.inputs[1] <== node1Right;
    signal level1 <== level1Hash.out;

    // Level 2
    component level2Hash = Poseidon(2);
    component mux2Left = Mux1();
    mux2Left.c[0] <== level1;
    mux2Left.c[1] <== merklePath[2];
    mux2Left.s <== pathIndices[2];
    signal node2Left <== mux2Left.out;

    component mux2Right = Mux1();
    mux2Right.c[0] <== merklePath[2];
    mux2Right.c[1] <== level1;
    mux2Right.s <== pathIndices[2];
    signal node2Right <== mux2Right.out;

    level2Hash.inputs[0] <== node2Left;
    level2Hash.inputs[1] <== node2Right;
    signal level2 <== level2Hash.out;

    // Level 3
    component level3Hash = Poseidon(2);
    component mux3Left = Mux1();
    mux3Left.c[0] <== level2;
    mux3Left.c[1] <== merklePath[3];
    mux3Left.s <== pathIndices[3];
    signal node3Left <== mux3Left.out;

    component mux3Right = Mux1();
    mux3Right.c[0] <== merklePath[3];
    mux3Right.c[1] <== level2;
    mux3Right.s <== pathIndices[3];
    signal node3Right <== mux3Right.out;

    level3Hash.inputs[0] <== node3Left;
    level3Hash.inputs[1] <== node3Right;
    signal level3 <== level3Hash.out;

    // Level 4
    component level4Hash = Poseidon(2);
    component mux4Left = Mux1();
    mux4Left.c[0] <== level3;
    mux4Left.c[1] <== merklePath[4];
    mux4Left.s <== pathIndices[4];
    signal node4Left <== mux4Left.out;

    component mux4Right = Mux1();
    mux4Right.c[0] <== merklePath[4];
    mux4Right.c[1] <== level3;
    mux4Right.s <== pathIndices[4];
    signal node4Right <== mux4Right.out;

    level4Hash.inputs[0] <== node4Left;
    level4Hash.inputs[1] <== node4Right;
    signal level4 <== level4Hash.out;

    // Level 5
    component level5Hash = Poseidon(2);
    component mux5Left = Mux1();
    mux5Left.c[0] <== level4;
    mux5Left.c[1] <== merklePath[5];
    mux5Left.s <== pathIndices[5];
    signal node5Left <== mux5Left.out;

    component mux5Right = Mux1();
    mux5Right.c[0] <== merklePath[5];
    mux5Right.c[1] <== level4;
    mux5Right.s <== pathIndices[5];
    signal node5Right <== mux5Right.out;

    level5Hash.inputs[0] <== node5Left;
    level5Hash.inputs[1] <== node5Right;
    signal level5 <== level5Hash.out;

    // Level 6
    component level6Hash = Poseidon(2);
    component mux6Left = Mux1();
    mux6Left.c[0] <== level5;
    mux6Left.c[1] <== merklePath[6];
    mux6Left.s <== pathIndices[6];
    signal node6Left <== mux6Left.out;

    component mux6Right = Mux1();
    mux6Right.c[0] <== merklePath[6];
    mux6Right.c[1] <== level5;
    mux6Right.s <== pathIndices[6];
    signal node6Right <== mux6Right.out;

    level6Hash.inputs[0] <== node6Left;
    level6Hash.inputs[1] <== node6Right;
    signal level6 <== level6Hash.out;

    // Level 7 (final)
    component level7Hash = Poseidon(2);
    component mux7Left = Mux1();
    mux7Left.c[0] <== level6;
    mux7Left.c[1] <== merklePath[7];
    mux7Left.s <== pathIndices[7];
    signal node7Left <== mux7Left.out;

    component mux7Right = Mux1();
    mux7Right.c[0] <== merklePath[7];
    mux7Right.c[1] <== level6;
    mux7Right.s <== pathIndices[7];
    signal node7Right <== mux7Right.out;

    level7Hash.inputs[0] <== node7Left;
    level7Hash.inputs[1] <== node7Right;
    signal level7 <== level7Hash.out;

    // Verify merkle root matches
    level7 === merkleRoot;

    // Step 3: Verify threshold constraint
    component gte = GreaterEqThan(14);
    gte.in[0] <== agentScore;
    gte.in[1] <== threshold;
    gte.out === 1;
}

component main { public [merkleRoot, threshold] } = MeritThreshold();
