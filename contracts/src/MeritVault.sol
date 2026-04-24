// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/// @notice Merit-weighted distribution vault (Base Sepolia, chainId 84532)
/// Supports KeeperHub 3-step workflow: CHECK → VALIDATE → EXECUTE
contract MeritVault {
    address public immutable owner;

    // merit scores scaled 1e4 (alice=2641, bob=6703, carol=0)
    mapping(address => uint256) public allocation;
    bool public validated;
    bool public executed;

    event Deposited(address indexed from, uint256 amount);
    event Allocated(address indexed account, uint256 amount);
    event WorkflowExecuted(uint256 totalDistributed);

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    receive() external payable {
        emit Deposited(msg.sender, msg.value);
    }

    /// CHECK — KeeperHub step 1: verify merit threshold met
    function check(address account, uint256 threshold) external view returns (bool) {
        return allocation[account] >= threshold;
    }

    /// VALIDATE — KeeperHub step 2: confirm on-chain allocation exists
    function validate(address account) external returns (bool ok) {
        ok = allocation[account] > 0;
        if (ok) validated = true;
    }

    /// EXECUTE — KeeperHub step 3: distribute ETH by merit weight
    function execute(
        address[] calldata accounts,
        uint256[] calldata merits   // scaled 1e4
    ) external onlyOwner {
        require(validated, "validate first");
        require(accounts.length == merits.length, "length mismatch");

        uint256 total = address(this).balance;
        uint256 sumMerit;
        for (uint256 i = 0; i < merits.length; i++) sumMerit += merits[i];
        require(sumMerit > 0, "no merit");

        uint256 distributed;
        for (uint256 i = 0; i < accounts.length; i++) {
            if (merits[i] == 0) continue;
            uint256 share = (total * merits[i]) / sumMerit;
            allocation[accounts[i]] += share;
            emit Allocated(accounts[i], share);
            distributed += share;
        }
        executed = true;
        emit WorkflowExecuted(distributed);
    }
}
