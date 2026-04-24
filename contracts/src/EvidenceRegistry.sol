// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/// @notice On-chain evidence anchor — stores root hashes for off-chain data
contract EvidenceRegistry {
    address public immutable owner;

    struct Evidence {
        bytes32 rootHash;
        string  label;
        uint256 anchoredAt;
    }

    Evidence[] public entries;

    event Anchored(uint256 indexed id, bytes32 indexed rootHash, string label);

    modifier onlyOwner() {
        require(msg.sender == owner, "not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function anchor(bytes32 rootHash, string calldata label) external onlyOwner returns (uint256 id) {
        id = entries.length;
        entries.push(Evidence(rootHash, label, block.number));
        emit Anchored(id, rootHash, label);
    }

    function latest() external view returns (bytes32 rootHash, string memory label, uint256 anchoredAt) {
        require(entries.length > 0, "empty");
        Evidence storage e = entries[entries.length - 1];
        return (e.rootHash, e.label, e.anchoredAt);
    }

    function count() external view returns (uint256) {
        return entries.length;
    }
}
