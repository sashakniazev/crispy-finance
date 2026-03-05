from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_account(client: AsyncClient):
    response = await client.post("/accounts", json={"name": "Cash", "type": "ASSET"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cash"
    assert data["type"] == "ASSET"
    assert data["balance"] == "0"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_account_duplicate_name(client: AsyncClient):
    await client.post("/accounts", json={"name": "Cash", "type": "ASSET"})
    response = await client.post("/accounts", json={"name": "Cash", "type": "LIABILITY"})

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_account(client: AsyncClient):
    create = await client.post("/accounts", json={"name": "Bank", "type": "ASSET"})
    account_id = create.json()["id"]

    response = await client.get(f"/accounts/{account_id}")

    assert response.status_code == 200
    assert response.json()["id"] == account_id


@pytest.mark.asyncio
async def test_get_account_not_found(client: AsyncClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/accounts/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_accounts(client: AsyncClient):
    await client.post("/accounts", json={"name": "Revenue", "type": "REVENUE"})
    await client.post("/accounts", json={"name": "Expenses", "type": "EXPENSE"})

    response = await client.get("/accounts")

    assert response.status_code == 200
    assert len(response.json()) >= 2
