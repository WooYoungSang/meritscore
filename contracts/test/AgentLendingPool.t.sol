// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {AgentLendingPool} from "../examples/AgentLendingPool.sol";
import {IMeritVault} from "../interfaces/IMeritVault.sol";

contract MockMeritVault is IMeritVault {
    mapping(address => uint256) public scores;
    function setScore(address a, uint256 s) external { scores[a] = s; }
    function getScore(address a) external view override returns (uint256) { return scores[a]; }
}

contract MockERC20 {
    mapping(address => uint256) public balanceOf;
    function mint(address to, uint256 amt) external { balanceOf[to] += amt; }
    function approve(address spender, uint256 amount) external returns (bool) {
        // MockERC20 ignores approval; transferFrom doesn't check it
        return true;
    }
    function transfer(address to, uint256 amt) external returns (bool) {
        balanceOf[msg.sender] -= amt;
        balanceOf[to] += amt;
        return true;
    }
    function transferFrom(address from, address to, uint256 amt) external returns (bool) {
        balanceOf[from] -= amt;
        balanceOf[to] += amt;
        return true;
    }
}

/// @dev Harness exposes internal _ltvFor for direct testing of merit-bucket logic
contract LendingPoolHarness is AgentLendingPool {
    constructor(address _merit, address _asset) AgentLendingPool(_merit, _asset) {}
    function ltvFor(uint256 score) external pure returns (uint256) {
        return _ltvFor(score);
    }
}

contract AgentLendingPoolTest is Test {
    LendingPoolHarness pool;
    MockMeritVault meritVault;
    MockERC20 token;
    address bob = address(0xB0B);
    address alice = address(0xA11CE);

    function setUp() public {
        meritVault = new MockMeritVault();
        token = new MockERC20();
        pool = new LendingPoolHarness(address(meritVault), address(token));
    }

    /// Ensures 1e4-scale thresholds (8000/6000), not the 800/600 bug from Codex review
    function test_LtvBuckets_OnCorrectScale() public view {
        assertEq(pool.ltvFor(9000), 7500); // top tier (>= 8000)
        assertEq(pool.ltvFor(8000), 7500); // boundary
        assertEq(pool.ltvFor(7000), 6000); // mid tier (>= 6000)
        assertEq(pool.ltvFor(6703), 6000); // Bob's actual score
        assertEq(pool.ltvFor(6000), 6000); // boundary
        assertEq(pool.ltvFor(5000), 4000); // floor tier
        assertEq(pool.ltvFor(2641), 4000); // Alice's score
        assertEq(pool.ltvFor(0),    4000); // Carol's score
    }

    function test_RejectLowMerit() public {
        meritVault.setScore(alice, 2641);
        token.mint(alice, 1000);
        vm.startPrank(alice);
        vm.expectRevert("LendingPool: agent merit too low");
        pool.borrow(100);
        vm.stopPrank();
    }

    function test_BobBorrowPositivePath() public {
        // Set Bob's merit score = 6703 → expected ltv bucket = 6000
        meritVault.setScore(bob, 6703);
        assertEq(pool.ltvFor(6703), 6000);

        // Mint Bob 1000 collateral tokens
        token.mint(bob, 1000);

        // Mint pool 10_000 tokens so it has liquidity to lend
        token.mint(address(pool), 10_000);

        // Bob deposits collateral
        vm.startPrank(bob);
        token.approve(address(pool), 1000); // MockERC20 ignores approval, but good practice
        pool.depositCollateral(1000);
        assertEq(pool.collateral(bob), 1000);

        // maxBorrow = (1000 * 6000) / 10000 = 600
        // Bob borrows 600 (at limit)
        pool.borrow(600);
        assertEq(pool.debt(bob), 600);
        assertEq(token.balanceOf(bob), 600); // received borrowed tokens

        // Attempting to borrow 1 more should revert (already at LTV limit)
        vm.expectRevert("LTV exceeded");
        pool.borrow(1);

        vm.stopPrank();
    }

    function test_BobBorrowExceedsLtvReverts() public {
        // Set Bob's merit score = 6703 → expected ltv bucket = 6000
        meritVault.setScore(bob, 6703);

        // Mint Bob 1000 collateral tokens
        token.mint(bob, 1000);

        // Mint pool 10_000 tokens so it has liquidity
        token.mint(address(pool), 10_000);

        // Bob deposits collateral
        vm.startPrank(bob);
        token.approve(address(pool), 1000);
        pool.depositCollateral(1000);

        // maxBorrow = (1000 * 6000) / 10000 = 600
        // Attempting to borrow 601 should revert
        vm.expectRevert("LTV exceeded");
        pool.borrow(601);

        vm.stopPrank();
    }
}
