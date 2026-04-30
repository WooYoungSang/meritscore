// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import {Test} from "forge-std/Test.sol";
import {MeritCore} from "../src/MeritCore.sol";

contract MeritCoreTest is Test {
    MeritCore core;
    address alice = address(0xA11CE);
    address bob = address(0xB0B);

    function setUp() public {
        core = new MeritCore();
    }

    function test_OwnerIsDeployer() public view {
        assertEq(core.owner(), address(this));
    }

    function test_SetAndReadMerit() public {
        core.setMerit(bob, 6703);
        (uint256 score, bool exists) = core.meritOf(bob);
        assertEq(score, 6703);
        assertTrue(exists);
    }

    function test_BatchSetMerit() public {
        address[] memory accounts = new address[](2);
        uint256[] memory scores = new uint256[](2);
        accounts[0] = alice;
        accounts[1] = bob;
        scores[0] = 2641;
        scores[1] = 6703;
        core.batchSetMerit(accounts, scores);

        (uint256 a,) = core.meritOf(alice);
        (uint256 b,) = core.meritOf(bob);
        assertEq(a, 2641);
        assertEq(b, 6703);
    }

    function test_OnlyOwnerCanSet() public {
        vm.prank(address(0xDEAD));
        vm.expectRevert("not owner");
        core.setMerit(bob, 1000);
    }
}
