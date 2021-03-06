import datetime

import pytest
from eth_utils import to_wei
from web3.contract import Contract

from ico.tests.utils import time_travel


@pytest.fixture
def preico_starts_at() -> int:
    """When pre-ico opens"""
    return int(datetime.datetime(2017, 1, 1).timestamp())


@pytest.fixture
def preico_ends_at() -> int:
    """When pre-ico closes"""
    return int(datetime.datetime(2017, 1, 3).timestamp())


@pytest.fixture
def preico_token_price() -> int:
    """Tokens per ether"""
    return to_wei(1, "ether") // 1200


@pytest.fixture
def preico_funding_goal() -> int:
    """Pre-ico funding goal is 1000 ETH."""
    return to_wei(1000, "ether")


@pytest.fixture
def preico_cap() -> int:
    """Pre-ico funding goal is 1000 ETH."""
    return to_wei(5000, "ether")


@pytest.fixture
def preico_token_allocation(token) -> int:
    """How many tokens we have allocated to be sold in pre-ico."""
    return int(token.call().totalSupply() * 0.1)


@pytest.fixture
def flat_pricing(chain, preico_token_price) -> Contract:
    """Flat pricing contact."""
    args = [
        preico_token_price,
    ]
    pricing_strategy, hash = chain.provider.deploy_contract('FlatPricing', deploy_args=args)
    return pricing_strategy


@pytest.fixture
def ico(chain, beneficiary, team_multisig, preico_starts_at, preico_ends_at, flat_pricing, preico_cap, preico_funding_goal, preico_token_allocation, token) -> Contract:
    """Create a Pre-ICO crowdsale contract."""

    args = [
        token.address,
        flat_pricing.address,
        team_multisig,
        beneficiary,
        preico_starts_at,
        preico_ends_at,
        preico_funding_goal,
        preico_cap
    ]

    tx = {
        "from": team_multisig,
    }

    contract, hash = chain.provider.deploy_contract('ICO', deploy_args=args, deploy_transaction=tx)

    assert contract.call().owner() == team_multisig

    # Allow pre-ico contract to do transferFrom()
    token.transact({"from": team_multisig}).setTransferAgent(contract.address, True)

    # Set aside the pool of tokens for pre-ico sale
    token.transact({"from": team_multisig}).approve(contract.address, preico_token_allocation)

    return contract


@pytest.fixture
def uncapped_token(empty_token):
    return empty_token


@pytest.fixture
def uncapped_flatprice(chain, beneficiary, team_multisig, preico_starts_at, preico_ends_at, flat_pricing, preico_cap, preico_funding_goal, preico_token_allocation, uncapped_token) -> Contract:
    """Create a Pre-ICO crowdsale contract."""

    token = uncapped_token

    args = [
        token.address,
        flat_pricing.address,
        team_multisig,
        beneficiary,
        preico_starts_at,
        preico_ends_at,
        preico_funding_goal,
    ]

    tx = {
        "from": team_multisig,
    }

    contract, hash = chain.provider.deploy_contract('UncappedCrowdsale', deploy_args=args, deploy_transaction=tx)

    assert contract.call().owner() == team_multisig
    assert not token.call().released()

    # Allow pre-ico contract to do mint()
    token.transact({"from": team_multisig}).setMintAgent(contract.address, True)
    assert token.call().mintAgents(contract.address) == True

    return contract


@pytest.fixture
def uncapped_flatprice_goal_reached(chain, uncapped_flatprice, preico_funding_goal, preico_starts_at, customer) -> Contract:
    """A ICO contract where the minimum funding goal has been reached."""
    time_travel(chain, preico_starts_at + 1)
    wei_value = preico_funding_goal
    uncapped_flatprice.transact({"from": customer, "value": wei_value}).buy()
    return uncapped_flatprice



