def test_user_can_be_linked_to_one_graduate(app):
    from app import Graduate, User, db
    with app.app_context():
        graduate = Graduate(student_no="2026999", name="李四")
        user = User(username="link-test", role="student", graduate=graduate)
        user.set_password("pw")
        db.session.add(user)
        db.session.commit()
        assert User.query.filter_by(username="link-test").one().graduate.name == "李四"


def test_student_login_redirects_to_student_dashboard(client):
    response = client.post("/login", data={"username": "student001", "password": "123456"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/student")


def test_student_cannot_open_staff_records(logged_in_student):
    response = logged_in_student.get("/staff/records", follow_redirects=True)
    assert "无权访问" in response.get_data(as_text=True)


def test_student_submission_creates_pending_employment(logged_in_student, app):
    response = logged_in_student.post("/student/employment/new", data={
        "employment_date": "2026-07-01", "employer": "示例科技有限公司",
        "employer_type": "民营企业", "position": "软件工程师",
        "archive_destination": "杭州市人才服务中心", "remark": "",
    }, follow_redirects=True)
    assert "就业信息已保存，等待审核" in response.get_data(as_text=True)
    with app.app_context():
        from app import Employment
        assert Employment.query.one().status == "pending"


def test_staff_can_approve_employment(logged_in_staff, pending_employment, app):
    response = logged_in_staff.post(f"/staff/employment/{pending_employment.id}/review", data={
        "status": "approved", "review_comment": "材料完整",
    }, follow_redirects=True)
    assert "审核完成" in response.get_data(as_text=True)
    with app.app_context():
        from app import Employment, db
        assert db.session.get(Employment, pending_employment.id).status == "approved"


def test_statistics_shows_approved_count(logged_in_staff, approved_employment):
    response = logged_in_staff.get("/staff/statistics")
    assert "审核通过" in response.get_data(as_text=True)


def test_init_demo_data_creates_both_demo_accounts(app):
    from app import User, db, init_demo_data
    with app.app_context():
        db.drop_all(); db.create_all(); init_demo_data()
        assert User.query.filter_by(username="student001").one().role == "student"
        assert User.query.filter_by(username="admin").one().role == "staff"
