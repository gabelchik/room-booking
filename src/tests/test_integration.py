import pytest
from httpx import AsyncClient
import datetime
from zoneinfo import ZoneInfo


ADMIN_UUID = "11111111-1111-1111-1111-111111111111"
USER_UUID = "22222222-2222-2222-2222-222222222222"


@pytest.mark.asyncio
async def test_full_booking_flow(client: AsyncClient):
    resp = await client.post("/dummyLogin", json={"role": "admin"})
    assert resp.status_code == 200
    admin_token = resp.json()["token"]
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    room_data = {"name": "Test Room", "description": "Test", "capacity": 10}
    resp = await client.post("/rooms/create", json=room_data, headers=headers_admin)
    assert resp.status_code == 201
    room_id = resp.json()["id"]

    schedule_data = {
        "days_of_week": [1, 2, 3, 4, 5],
        "start_time": "09:00",
        "end_time": "10:00"
    }
    resp = await client.post(f"/rooms/{room_id}/schedule/create",
                             json=schedule_data, headers=headers_admin)
    assert resp.status_code == 201

    resp = await client.post("/dummyLogin", json={"role": "user"})
    assert resp.status_code == 200
    user_token = resp.json()["token"]
    headers_user = {"Authorization": f"Bearer {user_token}"}

    today = datetime.datetime.now(ZoneInfo("UTC")).date()
    days_to_monday = (0 - today.weekday()) % 7
    if days_to_monday == 0:
        days_to_monday = 7
    target_date = today + datetime.timedelta(days=days_to_monday)
    date_str = target_date.isoformat()

    resp = await client.get(f"/rooms/{room_id}/slots/list?date={date_str}",
                            headers=headers_user)
    assert resp.status_code == 200
    slots = resp.json()
    assert len(slots) == 2
    slot_id = slots[0]["id"]

    booking_data = {"slot_id": slot_id}
    resp = await client.post("/bookings/create",
                             json=booking_data, headers=headers_user)
    assert resp.status_code == 201
    booking = resp.json()
    assert booking["status"] == "active"
    booking_id = booking["id"]
    assert booking["user_id"] == USER_UUID

    resp = await client.get(f"/rooms/{room_id}/slots/list?date={date_str}",
                            headers=headers_user)
    available_slots = resp.json()
    assert not any(s["id"] == slot_id for s in available_slots)

    resp = await client.post(f"/bookings/{booking_id}/cancel",
                             headers=headers_user)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"

    resp = await client.get(f"/rooms/{room_id}/slots/list?date={date_str}",
                            headers=headers_user)
    available_slots = resp.json()
    assert any(s["id"] == slot_id for s in available_slots)