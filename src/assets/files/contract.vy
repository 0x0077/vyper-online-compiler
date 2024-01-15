# @version 0.3.9
"""
@title Default code
@author 0x77
@license Copyright (c) VyperOnline, 2023-2025 - all rights reserved
"""

owner: public(address)
name: public(String[12])


@payable
@external
def __init__(_a: address, _b: address):
	self.owner = msg.sender
	self.name = "Hello Vyper!"


@view
@external
def test_add(_x: uint256, _y: uint256) -> uint256:
	return _x + _y