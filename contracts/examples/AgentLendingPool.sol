// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IMeritVault} from "../interfaces/IMeritVault.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/// @title Agent Lending Pool (warvis-hackerton integration example)
/// @notice Only approved agents above merit threshold can borrow
contract AgentLendingPool {
    IMeritVault public immutable merit;
    IERC20 public immutable asset;

    uint256 public constant MIN_MERIT = 500; // 0.500 on 0-1000 scale
    uint256 public constant MAX_LTV_BPS = 7500;

    mapping(address => uint256) public collateral;
    mapping(address => uint256) public debt;

    event AgentBorrowed(address agent, uint256 amount, uint256 meritScore);

    constructor(address _merit, address _asset) {
        merit = IMeritVault(_merit);
        asset = IERC20(_asset);
    }

    function borrow(uint256 amount) external {
        uint256 score = merit.getScore(msg.sender);
        require(score >= MIN_MERIT, "LendingPool: agent merit too low");
        uint256 maxBorrow = (collateral[msg.sender] * _ltvFor(score)) / 10000;
        require(debt[msg.sender] + amount <= maxBorrow, "LTV exceeded");
        debt[msg.sender] += amount;
        asset.transfer(msg.sender, amount);
        emit AgentBorrowed(msg.sender, amount, score);
    }

    function _ltvFor(uint256 score) internal pure returns (uint256) {
        if (score >= 800) return 7500;
        if (score >= 600) return 6000;
        return 4000;
    }

    function depositCollateral(uint256 amount) external {
        asset.transferFrom(msg.sender, address(this), amount);
        collateral[msg.sender] += amount;
    }
}
