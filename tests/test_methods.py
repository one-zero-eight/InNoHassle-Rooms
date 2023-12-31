from datetime import timedelta, datetime

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import delete, text

from src.api.auth.utils import create_jwt
from src.config import get_settings
from src.db_sessions.sqlalchemy_session import sessionmaker
from src.main import app
from src.models.sql import User, Room, Task, Order, TaskExecutor, Invitation

client = TestClient(app)

TOKEN = create_jwt({"sub": "tgbot"}, timedelta(minutes=5))


def post(url: str, json: dict) -> Response:
    return client.post(url, json=json, headers={"X-Token": TOKEN})


@pytest_asyncio.fixture(autouse=True)
async def setup_data_in_db():
    async with sessionmaker.get_session() as session:
        await session.execute(delete(Invitation))
        await session.execute(delete(TaskExecutor))
        await session.execute(delete(Order))
        await session.execute(delete(Task))
        await session.execute(delete(Room))
        await session.execute(delete(User))
        await session.commit()

        # IMPORTANT: be careful with default autoincrement and fixed IDs
        session.add(User(1, 1))
        session.add(User(2, 1))
        session.add(User(3))
        session.add(User(4, 2))
        session.add(User(5))
        session.add(Room(1, "room1"))
        session.add(Room(2, "room2"))
        session.add(Invitation(1, 1, 3, 1))
        session.add(Invitation(2, 1, 4, 2))
        session.add(Order(1, 1))
        session.add(TaskExecutor(2, 1, 0))
        session.add(TaskExecutor(1, 1, 1))
        session.add(Task(1, "task1", "bla-bla", 1, datetime.now() - timedelta(hours=12), 1, 1))
        await session.commit()

        if "postgresql" in get_settings().DB_URL:
            for table in ("rooms", "invitations", "orders", "tasks"):
                await session.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), ( SELECT MAX(id) FROM {table} ) + 1);"
                    )
                )
        await session.commit()


def test_register_exists():
    r = post("/bot/user/create", {"user_id": 1})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 101


def test_create_room_user_not_exist():
    r = post("/bot/room/create", {"user_id": 0, "room": {"name": "a"}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 102


def test_invite_person_user_not_exist():
    r = post("/bot/user/invite", {"user_id": 0, "addressee": {"id": 1}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 102


def test_accept_invitation_user_not_exist():
    r = post("/bot/user/accept_invitation", {"user_id": 0, "invitation": {"id": 1}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 102


def test_create_order_user_not_exist():
    r = post("/bot/order/create", {"user_id": 0, "order": {"users": [1]}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 102


def test_create_task_user_not_exist():
    r = post("/bot/task/create", {"user_id": 0, "task": {"name": "a", "start_date": 0, "period": 1, "order_id": 1}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 102


def test_modify_task_user_not_exist():
    r = post(
        "/bot/task/modify", {"user_id": 0, "task": {"id": 1, "name": "a", "start_date": 0, "period": 1, "order_id": 1}}
    )
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 102


def test_daily_info_user_not_exist():
    r = post("/bot/room/daily_info", {"user_id": 0})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 102


def test_create_room_user_has_room():
    r = post("/bot/room/create", {"user_id": 1, "room": {"name": "a"}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 106


def test_invite_user_addressee_has_room():
    r = post("/bot/user/invite", {"user_id": 1, "addressee": {"id": 2}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 106


def test_accept_invitation_user_has_room():
    r = post("/bot/user/accept_invitation", {"user_id": 4, "invitation": {"id": 2}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 106


def test_invite_user_user_has_no_room():
    r = post("/bot/user/invite", {"user_id": 3, "addressee": {"id": 2}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 105


def test_create_order_user_has_no_room():
    r = post("/bot/order/create", {"user_id": 3, "order": {"users": [1]}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 105


def test_create_task_user_has_no_room():
    r = post("/bot/task/create", {"user_id": 3, "task": {"name": "a", "start_date": 0, "period": 1, "order_id": 1}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 105


def test_modify_task_user_has_no_room():
    r = post(
        "/bot/task/modify", {"user_id": 3, "task": {"id": 1, "name": "a", "start_date": 0, "period": 1, "order_id": 1}}
    )
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 105


def test_daily_info_user_has_no_room():
    r = post("/bot/room/daily_info", {"user_id": 3})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 105


@pytest.mark.asyncio
async def test_invite_too_many():
    async with sessionmaker.get_session() as db:
        db.add(Room(1001, "1001"))
        db.add(User(1001, 1001))
        for i in range(get_settings().MAX_INVITATIONS):
            db.add(Invitation(id_=1001 + i, sender_id=1001, addressee_id=1, room_id=1001))
        await db.commit()
    r = post("/bot/user/invite", {"user_id": 1001, "addressee": {"id": 3}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 109


@pytest.mark.asyncio
async def test_create_order_too_many():
    async with sessionmaker.get_session() as db:
        db.add(Room(1001, "1001"))
        db.add(User(1001, 1001))
        for i in range(get_settings().MAX_ORDERS):
            db.add(Order(id_=1001 + i, room_id=1001))
        await db.commit()
    r = post("/bot/order/create", {"user_id": 1001, "order": {"users": [1001]}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 113


@pytest.mark.asyncio
async def test_create_task_too_many():
    async with sessionmaker.get_session() as db:
        db.add(Room(1001, "1001"))
        db.add(User(1001, 1001))
        db.add(Order(1001, 1001))
        for i in range(get_settings().MAX_TASKS):
            db.add(Task(id_=1001 + i, name="1001", start_date=datetime.fromtimestamp(0), period=1, room_id=1001))
        await db.commit()
    r = post(
        "/bot/task/create",
        {"user_id": 1001, "task": {"name": "1001", "start_date": 0, "period": 1, "order_id": "1001"}},
    )
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 114


def test_invite_already_sent():
    r = post("/bot/user/invite", {"user_id": 1, "addressee": {"id": 3}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 110


def test_accept_invitation_not_exist():
    r = post("/bot/user/accept_invitation", {"user_id": 3, "invitation": {"id": 0}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 111


def test_accept_invitation_not_yours():
    r = post("/bot/user/accept_invitation", {"user_id": 5, "invitation": {"id": 1}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 112


def test_create_order_user_in_order_not_exist():
    r = post("/bot/order/create", {"user_id": 1, "order": {"users": [0]}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 116


def test_create_order_order_user_not_in_room():
    r = post("/bot/order/create", {"user_id": 1, "order": {"users": [3]}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 115


def test_create_task_order_not_exist():
    r = post("/bot/task/create", {"user_id": 1, "task": {"name": "one", "start_date": 0, "period": 1, "order_id": 0}})
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 107


def test_modify_task_not_exist():
    r = post(
        "/bot/task/modify",
        {"user_id": 1, "task": {"id": 0, "name": "one", "start_date": 0, "period": 1, "order_id": 1}},
    )
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 108


def test_modify_task_order_not_exist():
    r = post(
        "/bot/task/modify",
        {"user_id": 1, "task": {"id": 1, "name": "one", "start_date": 0, "period": 1, "order_id": 0}},
    )
    assert r.status_code == 400 and isinstance(r.json(), dict) and "code" in r.json()
    assert r.json()["code"] == 107


def test_register():
    r = post("/bot/user/create", {"user_id": 1001})
    assert r.status_code == 200 and r.json() == 1001


@pytest.mark.asyncio
async def test_create_room():
    async with sessionmaker.get_session() as db:
        db.add(User(1001))
        await db.commit()
    r = post("/bot/room/create", {"user_id": 1001, "room": {"name": "1001"}})
    assert r.status_code == 200 and isinstance(r.json(), int)


@pytest.mark.asyncio
async def test_invite():
    async with sessionmaker.get_session() as db:
        db.add(User(1001, 1001))
        db.add(Room(1001, "1001"))
        await db.commit()
    r = post("/bot/user/invite", {"user_id": 1001, "addressee": {"id": 1002}})
    assert r.status_code == 200 and isinstance(r.json(), int)


@pytest.mark.asyncio
async def test_accept_invitation():
    async with sessionmaker.get_session() as db:
        db.add(User(1001, 1001))
        db.add(User(1002))
        db.add(Room(1001, "1001"))
        db.add(Invitation(1001, 1001, 1002, 1001))
        await db.commit()
    r = post("/bot/user/accept_invitation", {"user_id": 1002, "invitation": {"id": 1001}})
    assert r.status_code == 200 and r.json() == 1001


@pytest.mark.asyncio
async def test_create_order():
    async with sessionmaker.get_session() as db:
        db.add(User(1001, 1001))
        db.add(User(1002, 1001))
        db.add(Room(1001, "1001"))
        await db.commit()
    r = post("/bot/order/create", {"user_id": 1001, "order": {"users": [1002, 1001]}})
    assert r.status_code == 200 and isinstance(r.json(), int)


@pytest.mark.asyncio
async def test_create_task():
    async with sessionmaker.get_session() as db:
        db.add(User(1001, 1001))
        db.add(User(1002, 1001))
        db.add(Room(1001, "1001"))
        await db.commit()
    order_id = post("/bot/order/create", {"user_id": 1001, "order": {"users": [1002, 1001]}}).json()
    r = post(
        "/bot/task/create",
        {
            "user_id": 1001,
            "task": {
                "name": "task1001",
                "description": "foo bar",
                "start_date": datetime.now().isoformat(),
                "period": 7,
                "order_id": order_id,
            },
        },
    )
    assert r.status_code == 200 and isinstance(r.json(), int)


@pytest.mark.asyncio
async def test_modify_task():
    async with sessionmaker.get_session() as db:
        db.add(User(1001, 1001))
        db.add(Room(1001, "1001"))
        db.add(Order(1001, 1001))
        db.add(TaskExecutor(1001, 1001, 1))
        db.add(Task(1001, "1001", "", 1001, datetime.now(), 1, 1001))
        await db.commit()
    r = post(
        "/bot/task/modify",
        {
            "user_id": 1001,
            "task": {
                "id": 1001,
                "name": "task1001",
                "description": "foo bar",
                "start_date": datetime.now().isoformat(),
                "period": 7,
                "order_id": 1001,
            },
        },
    )
    assert r.status_code == 200 and r.json() is True


def test_daily_info():
    post("/bot/user/create", {"user_id": 1001})
    post("/bot/user/create", {"user_id": 1002})
    post("/bot/room/create", {"user_id": 1001, "room": {"name": "1001"}})
    invitation = post("/bot/user/invite", {"user_id": 1001, "addressee": {"id": 1002}}).json()
    post("/bot/user/accept_invitation", {"user_id": 1002, "invitation": {"id": invitation}})
    order_id = post("/bot/order/create", {"user_id": 1001, "order": {"users": [1001, 1002]}}).json()
    task1 = post(
        "/bot/task/create",
        {
            "user_id": 1001,
            "task": {
                "name": "task1001",
                "start_date": datetime.now().astimezone().isoformat(),
                "period": 1,
                "order_id": order_id,
            },
        },
    ).json()
    task2 = post(
        "/bot/task/create",
        {
            "user_id": 1001,
            "task": {
                "name": "task1002",
                "start_date": (datetime.now().astimezone() - timedelta(days=1)).isoformat(),
                "period": 1,
                "order_id": order_id,
            },
        },
    ).json()
    r = post("/bot/room/daily_info", {"user_id": 1001})
    assert r.status_code == 200 and (
        {"id": task1, "name": "task1001", "today_user_id": 1001} in (tasks := r.json()["tasks"])
        and {"id": task2, "name": "task1002", "today_user_id": 1002} in tasks
    )
