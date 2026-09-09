# 毕业生就业信息管理系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一个使用 Flask 和 SQLite 的毕业生就业信息演示系统，支持学生维护就业信息及工作人员审核和统计。

**Architecture:** 单个 Flask 应用承载路由、SQLAlchemy 模型与登录会话；Jinja2 模板构成学生端和工作人员端页面。SQLite 本地文件保存演示数据，pytest 通过应用工厂和临时数据库验证角色权限与核心流程。

**Tech Stack:** Python 3.10+、Flask、Flask-SQLAlchemy、Werkzeug、pytest、SQLite、HTML/CSS。

**Spec:** `docs/superpowers/specs/2026-09-09-graduate-employment-system-design.md`

## Global Constraints

- 仅使用 Flask、Flask-SQLAlchemy 和 pytest 作为第三方依赖。
- 运行命令为 `python app.py`，默认数据库文件为 `employment.db`。
- 学生仅能访问和修改与自身账号关联的就业记录。
- 保存学生就业信息后状态必须为 `pending`。
- 工作人员审核状态只能是 `approved` 或 `rejected`。
- 初始化演示账户固定为 `student001` / `123456` 与 `admin` / `admin123`。

---

## File Structure

- `app.py`：应用工厂、数据模型、认证/角色装饰器、所有页面路由、初始化命令。
- `templates/base.html`：导航栏、闪现消息和公共布局。
- `templates/login.html`：登录表单。
- `templates/student_dashboard.html`：学生个人信息、就业记录和编辑入口。
- `templates/employment_form.html`：就业信息新增/修改表单。
- `templates/staff_records.html`：工作人员就业记录检索与列表。
- `templates/review.html`：工作人员审核详情与审核表单。
- `templates/statistics.html`：审核状态与单位性质统计。
- `static/style.css`：所有页面的演示级样式。
- `tests/conftest.py`：临时数据库、测试客户端、演示账号夹具。
- `tests/test_employment_system.py`：认证、权限、提交、审核和统计的集成测试。
- `requirements.txt`：运行与测试依赖。
- `README.md`：安装、初始化、运行、演示账号与功能说明。

## Task 1: App Factory and Persistent Models

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_employment_system.py`
- Create: `app.py`
- Create: `requirements.txt`

**Interfaces:**
- Produces: `create_app(test_config: dict | None = None) -> Flask`
- Produces: models `User`, `Graduate`, `Employment`, global `db`
- Consumes: `app.app_context()` to create tables.

- [ ] **Step 1: Write the failing model test**

```python
def test_user_can_be_linked_to_one_graduate(app):
    from app import Graduate, User, db

    with app.app_context():
        graduate = Graduate(student_no="2026001", name="张三")
        user = User(username="student001", role="student", graduate=graduate)
        user.set_password("123456")
        db.session.add(user)
        db.session.commit()
        assert User.query.filter_by(username="student001").one().graduate.name == "张三"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_employment_system.py::test_user_can_be_linked_to_one_graduate -v`

Expected: FAIL because module `app` or model classes do not exist.

- [ ] **Step 3: Implement application factory and models**

```python
def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(SQLALCHEMY_DATABASE_URI="sqlite:///employment.db")
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    return app

class User(db.Model):
    graduate = db.relationship("Graduate", backref="user", uselist=False)
```

Add `Graduate` and `Employment` fields exactly as specified, plus password helpers using Werkzeug.

- [ ] **Step 4: Run the model test to verify it passes**

Run: `pytest tests/test_employment_system.py::test_user_can_be_linked_to_one_graduate -v`

Expected: PASS.

## Task 2: Login, Logout and Role Guards

**Files:**
- Modify: `tests/test_employment_system.py`
- Modify: `app.py`
- Create: `templates/base.html`
- Create: `templates/login.html`

**Interfaces:**
- Consumes: `User.check_password(password: str) -> bool`, session key `user_id`.
- Produces: `login_required(view)` and `role_required(role: str)` decorators.
- Produces: routes `/login`, `/logout`, `/`.

- [ ] **Step 1: Write failing authentication and permission tests**

```python
def test_student_login_redirects_to_student_dashboard(client):
    response = client.post("/login", data={"username": "student001", "password": "123456"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/student")

def test_student_cannot_open_staff_records(logged_in_student):
    response = logged_in_student.get("/staff/records", follow_redirects=True)
    assert "无权访问" in response.get_data(as_text=True)
```

- [ ] **Step 2: Run the authentication tests to verify they fail**

Run: `pytest tests/test_employment_system.py -k "login or cannot_open" -v`

Expected: FAIL because routes and decorators do not exist.

- [ ] **Step 3: Implement login workflow and guards**

```python
@app.post("/login")
def login():
    user = User.query.filter_by(username=request.form.get("username", "").strip()).first()
    if not user or not user.check_password(request.form.get("password", "")):
        flash("账号或密码错误", "error")
        return redirect(url_for("login"))
    session["user_id"] = user.id
    return redirect(url_for("student_dashboard" if user.role == "student" else "staff_records"))
```

Use `functools.wraps`; enforce login and role checks with flash messages and safe redirects.

- [ ] **Step 4: Run the authentication tests to verify they pass**

Run: `pytest tests/test_employment_system.py -k "login or cannot_open" -v`

Expected: PASS.

## Task 3: Student Employment Maintenance

**Files:**
- Modify: `tests/test_employment_system.py`
- Modify: `app.py`
- Create: `templates/student_dashboard.html`
- Create: `templates/employment_form.html`

**Interfaces:**
- Consumes: logged-in student `g.current_user.graduate`.
- Produces: `/student`, `/student/employment/new`, `/student/employment/edit`.
- Produces: exactly one `Employment` per `Graduate`.

- [ ] **Step 1: Write the failing student-submission test**

```python
def test_student_submission_creates_pending_employment(logged_in_student, app):
    response = logged_in_student.post("/student/employment/new", data={
        "employment_date": "2026-07-01", "employer": "示例科技有限公司",
        "employer_type": "民营企业", "position": "软件工程师",
        "archive_destination": "杭州市人才服务中心", "remark": "",
    }, follow_redirects=True)
    assert "就业信息已保存，等待审核" in response.get_data(as_text=True)
    with app.app_context():
        assert Employment.query.one().status == "pending"
```

- [ ] **Step 2: Run the student-submission test to verify it fails**

Run: `pytest tests/test_employment_system.py::test_student_submission_creates_pending_employment -v`

Expected: FAIL because student employment route does not exist.

- [ ] **Step 3: Implement student dashboard and form handling**

```python
required = ("employment_date", "employer", "employer_type", "archive_destination")
if any(not request.form.get(name, "").strip() for name in required):
    flash("请填写所有必填项", "error")
    return render_template("employment_form.html", employment=employment)
employment.status = "pending"
employment.review_comment = None
employment.reviewed_at = None
```

Render personal profile and existing record; update an existing record instead of creating a second one.

- [ ] **Step 4: Run the student-submission test to verify it passes**

Run: `pytest tests/test_employment_system.py::test_student_submission_creates_pending_employment -v`

Expected: PASS.

## Task 4: Staff Review, Search and Statistics

**Files:**
- Modify: `tests/test_employment_system.py`
- Modify: `app.py`
- Create: `templates/staff_records.html`
- Create: `templates/review.html`
- Create: `templates/statistics.html`

**Interfaces:**
- Produces: `/staff/records`, `/staff/employment/<int:employment_id>/review`, `/staff/statistics`.
- Consumes: `Employment.status` values `pending`, `approved`, `rejected`.
- Produces: aggregate context keys `counts` and `employer_type_stats`.

- [ ] **Step 1: Write failing review and statistics tests**

```python
def test_staff_can_approve_employment(logged_in_staff, pending_employment, app):
    response = logged_in_staff.post(f"/staff/employment/{pending_employment.id}/review", data={
        "status": "approved", "review_comment": "材料完整",
    }, follow_redirects=True)
    assert "审核完成" in response.get_data(as_text=True)
    with app.app_context():
        assert db.session.get(Employment, pending_employment.id).status == "approved"

def test_statistics_shows_approved_count(logged_in_staff, approved_employment):
    response = logged_in_staff.get("/staff/statistics")
    assert "审核通过" in response.get_data(as_text=True)
```

- [ ] **Step 2: Run review and statistics tests to verify they fail**

Run: `pytest tests/test_employment_system.py -k "approve or statistics" -v`

Expected: FAIL because staff routes do not exist.

- [ ] **Step 3: Implement staff record workflow**

```python
query = Employment.query.join(Graduate)
keyword = request.args.get("keyword", "").strip()
status = request.args.get("status", "").strip()
if keyword:
    query = query.filter(db.or_(Graduate.name.contains(keyword), Graduate.student_no.contains(keyword)))
if status in {"pending", "approved", "rejected"}:
    query = query.filter(Employment.status == status)
```

Validate posted review status, set `reviewed_at = datetime.utcnow()`, render review detail and calculate approved records grouped by `employer_type`.

- [ ] **Step 4: Run review and statistics tests to verify they pass**

Run: `pytest tests/test_employment_system.py -k "approve or statistics" -v`

Expected: PASS.

## Task 5: Styling, Demo Seed, Documentation and Full Verification

**Files:**
- Create: `static/style.css`
- Modify: `app.py`
- Create: `README.md`
- Modify: `tests/conftest.py`

**Interfaces:**
- Produces: `init_demo_data()` callable and command `flask --app app init-demo`.
- Produces: local startup instructions and account table in README.

- [ ] **Step 1: Write the failing seed-data test**

```python
def test_init_demo_data_creates_both_demo_accounts(app):
    from app import User, db, init_demo_data
    with app.app_context():
        db.drop_all(); db.create_all()
        init_demo_data()
        assert User.query.filter_by(username="student001").one().role == "student"
        assert User.query.filter_by(username="admin").one().role == "staff"
```

- [ ] **Step 2: Run the seed-data test to verify it fails**

Run: `pytest tests/test_employment_system.py::test_init_demo_data_creates_both_demo_accounts -v`

Expected: FAIL because the initializer does not exist.

- [ ] **Step 3: Implement seed command, styles and README**

```python
def init_demo_data():
    if User.query.filter_by(username="student001").first():
        return
    graduate = Graduate(student_no="2026001", name="张三", major="计算机科学与技术", class_name="计科2201班", phone="13800000000")
    student = User(username="student001", role="student", graduate=graduate)
    student.set_password("123456")
    staff = User(username="admin", role="staff")
    staff.set_password("admin123")
    db.session.add_all([student, staff]); db.session.commit()
```

Add responsive card, table, form, alert and status-badge styles. Document `pip install -r requirements.txt`, `flask --app app init-demo`, and `python app.py`.

- [ ] **Step 4: Run seed test and full verification**

Run: `pytest -v; python -m compileall app.py`

Expected: all tests PASS and compilation exits with code 0.

## Plan Self-Review

- Spec coverage: Task 1 maps all three models; Task 2 covers identity and role boundaries; Task 3 covers student viewing/submission/editing; Task 4 covers audit, search and aggregate statistics; Task 5 covers fixed demo credentials, styling, instructions and complete verification.
- Placeholder scan: no unbounded tasks or deferred requirements are present.
- Interface consistency: all routes, statuses and model names align with the design specification.
