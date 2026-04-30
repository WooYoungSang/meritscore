// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test} from "forge-std/Test.sol";
import {MeritVault} from "../src/MeritVault.sol";

contract MeritVaultTest is Test {
    MeritVault vault;
    address alice = address(0xA11CE);
    address bob = address(0xB0B);

    function setUp() public {
        vault = new MeritVault();
    }

    function test_SeedAndGetScore() public {
        address[] memory agents = new address[](2);
        uint256[] memory scores = new uint256[](2);
        agents[0] = alice;
        agents[1] = bob;
        scores[0] = 2641;
        scores[1] = 6703;
        vault.seedScores(agents, scores);

        assertEq(vault.getScore(alice), 2641);
        assertEq(vault.getScore(bob), 6703);
    }

    function test_CheckThreshold() public {
        address[] memory agents = new address[](1);
        uint256[] memory scores = new uint256[](1);
        agents[0] = bob;
        scores[0] = 6703;
        vault.seedScores(agents, scores);

        assertTrue(vault.check(bob, 5000));
        assertFalse(vault.check(bob, 7000));
    }
}
