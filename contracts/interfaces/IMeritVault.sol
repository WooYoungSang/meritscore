// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title IMeritVault
/// @notice Interface for reading merit scores from MeritVault
/// @dev Merit scores are stored as uint256 scaled 1e4 (0-10000 represents 0.0-1.0)
interface IMeritVault {
    /// @notice Get the merit score for an agent
    /// @param agent The agent address
    /// @return Merit score scaled 1e4 (e.g., 6703 = 0.6703)
    function getScore(address agent) external view returns (uint256);
}
