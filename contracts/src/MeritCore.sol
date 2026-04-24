// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/// @notice On-chain merit score registry (0G Galileo, chainId 16602)
contract MeritCore {
    address public immutable owner;

    struct MeritEntry {
        uint256 score;   // scaled 1e4 (e.g. 0.2641 → 2641)
        bool    exists;
    }

    mapping(address => MeritEntry) public meritOf;
    bytes32 public oracleCommitHash;
    uint256 public commitBlock;

    event MeritSet(address indexed account, uint256 score);
    event OracleCommit(bytes32 indexed commitHash, uint256 blockNumber);

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function setMerit(address account, uint256 score) external onlyOwner {
        meritOf[account] = MeritEntry(score, true);
        emit MeritSet(account, score);
    }

    function batchSetMerit(
        address[] calldata accounts,
        uint256[] calldata scores
    ) external onlyOwner {
        require(accounts.length == scores.length, "length mismatch");
        for (uint256 i = 0; i < accounts.length; i++) {
            meritOf[accounts[i]] = MeritEntry(scores[i], true);
            emit MeritSet(accounts[i], scores[i]);
        }
    }

    /// @notice Anchor oracle commit hash on-chain (CP4 evidence)
    function commitOracle(bytes32 commitHash) external onlyOwner {
        oracleCommitHash = commitHash;
        commitBlock = block.number;
        emit OracleCommit(commitHash, block.number);
    }
}
