import pytest
from io import BytesIO
from pathlib import Path
import uuid

from app import create_app, db, init_demo_data


@pytest.fixture()
def app():
    db_path = Path(__file__).parent / f"test-{uuid.uuid4().hex}.db"
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}",
        "SECRET_KEY": "test-secret",
    })
    with app.app_context():
        db.create_all()
        init_demo_data()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
    db_path.unlink(missing_ok=True)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def logged_in_student(app):
    isolated = app.test_client()
    isolated.post("/login", data={"username": "student001", "password": "123456"})
    return isolated


@pytest.fixture()
def logged_in_staff(app):
    isolated = app.test_client()
    isolated.post("/login", data={"username": "admin", "password": "admin123"})
    return isolated


@pytest.fixture()
def pending_employment(app, logged_in_student):
    logged_in_student.post("/student/employment/new", data={
        "employment_date": "2026-07-01", "employer": "示例科技有限公司",
        "employer_type": "民营企业", "position": "软件工程师",
        "archive_destination": "杭州市人才服务中心", "remark": "",
        "agreement_signed": "1",
        "agreement_file": (BytesIO(b"%PDF-1.7\ndemo agreement"), "demo-agreement.pdf"),
    }, content_type="multipart/form-data")
    with app.app_context():
        from app import Employment
        return db.session.get(Employment, 1)


@pytest.fixture()
def approved_employment(app, pending_employment, logged_in_staff):
    logged_in_staff.post(f"/staff/employment/{pending_employment.id}/review", data={
        "status": "approved", "review_comment": "材料完整",
    })
    return pending_employment
