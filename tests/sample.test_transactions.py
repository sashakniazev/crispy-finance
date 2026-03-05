from decimal import Decimal

import pytest
from httpx import AsyncClient


async def _create_account(client: AsyncClient, name: str, type_: str) -> str:
    response = await client.post("/accounts", json={"name": name, "type": type_})
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_valid_transaction(client: AsyncClient):
    asset_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    response = await client.post(
        "/transactions",
        json={
            "description": "Sale",
            "entries": [
                {"account_id": asset_id, "type": "DEBIT", "amount": "100.00"},
                {"account_id": revenue_id, "type": "CREDIT", "amount": "100.00"},
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Sale"
    assert len(data["entries"]) == 2
    assert "id" in data


@pytest.mark.asyncio
async def test_create_transaction_unbalanced(client: AsyncClient):
    asset_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    response = await client.post(
        "/transactions",
        json={
            "description": "Unbalanced",
            "entries": [
                {"account_id": asset_id, "type": "DEBIT", "amount": "100.00"},
                {"account_id": revenue_id, "type": "CREDIT", "amount": "50.00"},
            ],
        },
    )

    assert response.status_code == 400
    assert "Debits" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_transaction_only_debits(client: AsyncClient):
    asset_id = await _create_account(client, "Cash", "ASSET")
    expense_id = await _create_account(client, "Expenses", "EXPENSE")

    response = await client.post(
        "/transactions",
        json={
            "description": "Only debits",
            "entries": [
                {"account_id": asset_id, "type": "DEBIT", "amount": "50.00"},
                {"account_id": expense_id, "type": "DEBIT", "amount": "50.00"},
            ],
        },
    )

    assert response.status_code == 400
    assert "CREDIT" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_transaction_single_entry(client: AsyncClient):
    asset_id = await _create_account(client, "Cash", "ASSET")

    response = await client.post(
        "/transactions",
        json={
            "description": "Single entry",
            "entries": [
                {"account_id": asset_id, "type": "DEBIT", "amount": "100.00"},
            ],
        },
    )

    assert response.status_code == 400
    assert "2 entries" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_transaction_nonexistent_account(client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    asset_id = await _create_account(client, "Cash", "ASSET")

    response = await client.post(
        "/transactions",
        json={
            "description": "Bad account",
            "entries": [
                {"account_id": asset_id, "type": "DEBIT", "amount": "100.00"},
                {"account_id": fake_id, "type": "CREDIT", "amount": "100.00"},
            ],
        },
    )

    assert response.status_code == 400
    assert fake_id in response.json()["detail"]


@pytest.mark.asyncio
async def test_balance_after_transaction(client: AsyncClient):
    asset_id = await _create_account(client, "Cash", "ASSET")
    revenue_id = await _create_account(client, "Revenue", "REVENUE")

    await client.post(
        "/transactions",
        json={
            "description": "Sale",
            "entries": [
                {"account_id": asset_id, "type": "DEBIT", "amount": "200.00"},
                {"account_id": revenue_id, "type": "CREDIT", "amount": "200.00"},
            ],
        },
    )

    asset = await client.get(f"/accounts/{asset_id}")
    revenue = await client.get(f"/accounts/{revenue_id}")

    assert float(asset.json()["balance"]) == Decimal("200.00")
    assert float(revenue.json()["balance"]) == Decimal("200.00")


@pytest.mark.asyncio
async def test_get_transaction_not_found(client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/transactions/{fake_id}")

    assert response.status_code == 404
