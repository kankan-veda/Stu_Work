from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

import click
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class Graduate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_no = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    major = db.Column(db.String(100), nullable=False, default="")
    class_name = db.Column(db.String(100), nullable=False, default="")
    phone = db.Column(db.String(30), nullable=False, default="")
    employment = db.relationship("Employment", backref="graduate", uselist=False, cascade="all, delete-orphan")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    graduate_id = db.Column(db.Integer, db.ForeignKey("graduate.id"), unique=True, nullable=True)
    graduate = db.relationship("Graduate", backref=db.backref("user", uselist=False))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Employment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    graduate_id = db.Column(db.Integer, db.ForeignKey("graduate.id"), unique=True, nullable=False)
    employment_date = db.Column(db.String(20), nullable=False)
    employer = db.Column(db.String(200), nullable=False)
    employer_type = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(100), nullable=False, default="")
    archive_destination = db.Column(db.String(200), nullable=False)
    remark = db.Column(db.Text, nullable=False, default="")
    status = db.Column(db.String(20), nullable=False, default="pending")
    review_comment = db.Column(db.Text)
    reviewed_at = db.Column(db.DateTime)


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev-secret-change-me",
        SQLALCHEMY_DATABASE_URI="sqlite:///employment.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)
    db.init_app(app)

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.current_user = db.session.get(User, user_id) if user_id else None

    @app.context_processor
    def inject_user():
        return {"current_user": g.get("current_user")}

    @app.get("/")
    def index():
        if not g.current_user:
            return redirect(url_for("login"))
        return redirect(url_for("student_dashboard" if g.current_user.role == "student" else "staff_records"))

    @app.route("/login", methods=("GET", "POST"))
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = User.query.filter_by(username=username).first()
            if not user or not user.check_password(password):
                flash("账号或密码错误", "error")
            else:
                session.clear(); session["user_id"] = user.id
                return redirect(url_for("student_dashboard" if user.role == "student" else "staff_records"))
        return render_template("login.html")

    @app.route("/register", methods=("GET", "POST"))
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            student_no = request.form.get("student_no", "").strip()
            name = request.form.get("name", "").strip()
            major = request.form.get("major", "").strip()
            class_name = request.form.get("class_name", "").strip()
            phone = request.form.get("phone", "").strip()
            if not all((username, password, confirm_password, student_no, name, major, class_name, phone)):
                flash("请填写完整注册信息", "error")
                return render_template("register.html")
            if len(password) < 6:
                flash("密码至少需要 6 位", "error")
                return render_template("register.html")
            if password != confirm_password:
                flash("两次输入的密码不一致", "error")
                return render_template("register.html")
            if User.query.filter_by(username=username).first():
                flash("该账号已存在", "error")
                return render_template("register.html")
            if Graduate.query.filter_by(student_no=student_no).first():
                flash("该学号已注册", "error")
                return render_template("register.html")
            graduate = Graduate(student_no=student_no, name=name, major=major, class_name=class_name, phone=phone)
            user = User(username=username, role="student", graduate=graduate)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("注册成功，请登录", "success")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.get("/logout")
    def logout():
        session.clear(); return redirect(url_for("login"))

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not g.current_user:
                flash("请先登录", "error"); return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def role_required(role):
        def decorator(view):
            @wraps(view)
            @login_required
            def wrapped(*args, **kwargs):
                if g.current_user.role != role:
                    flash("无权访问该页面", "error")
                    return redirect(url_for("student_dashboard" if g.current_user.role == "student" else "staff_records"))
                return view(*args, **kwargs)
            return wrapped
        return decorator

    @app.get("/student")
    @role_required("student")
    def student_dashboard():
        return render_template("student_dashboard.html", graduate=g.current_user.graduate, employment=g.current_user.graduate.employment)

    @app.route("/student/employment/new", methods=("GET", "POST"))
    @role_required("student")
    def employment_new():
        employment = g.current_user.graduate.employment or Employment(graduate=g.current_user.graduate)
        return _save_employment(employment, "新增就业信息") if request.method == "POST" else render_template("employment_form.html", employment=employment, title="新增就业信息")

    @app.route("/student/employment/edit", methods=("GET", "POST"))
    @role_required("student")
    def employment_edit():
        employment = g.current_user.graduate.employment
        if not employment: return redirect(url_for("employment_new"))
        return _save_employment(employment, "修改就业信息") if request.method == "POST" else render_template("employment_form.html", employment=employment, title="修改就业信息")

    def _save_employment(employment, _title):
        required = ("employment_date", "employer", "employer_type", "archive_destination")
        if any(not request.form.get(name, "").strip() for name in required):
            flash("请填写所有必填项", "error")
            return render_template("employment_form.html", employment=employment, title=_title)
        for field in ("employment_date", "employer", "employer_type", "position", "archive_destination", "remark"):
            setattr(employment, field, request.form.get(field, "").strip())
        employment.status, employment.review_comment, employment.reviewed_at = "pending", None, None
        db.session.add(employment); db.session.commit()
        flash("就业信息已保存，等待审核", "success")
        return redirect(url_for("student_dashboard"))

    @app.get("/staff/records")
    @role_required("staff")
    def staff_records():
        query = Employment.query.join(Graduate)
        keyword, status = request.args.get("keyword", "").strip(), request.args.get("status", "").strip()
        if keyword: query = query.filter(or_(Graduate.name.contains(keyword), Graduate.student_no.contains(keyword)))
        if status in {"pending", "approved", "rejected"}: query = query.filter(Employment.status == status)
        return render_template("staff_records.html", records=query.order_by(Employment.id.desc()).all(), keyword=keyword, status=status)

    @app.route("/staff/employment/<int:employment_id>/review", methods=("GET", "POST"))
    @role_required("staff")
    def review_employment(employment_id):
        employment = db.session.get(Employment, employment_id)
        if not employment: abort(404)
        if request.method == "POST":
            new_status = request.form.get("status")
            if new_status not in {"approved", "rejected"}:
                flash("请选择审核结果", "error")
                return render_template("review.html", employment=employment)
            employment.status, employment.review_comment, employment.reviewed_at = new_status, request.form.get("review_comment", "").strip(), datetime.now(timezone.utc)
            db.session.commit(); flash("审核完成", "success"); return redirect(url_for("staff_records"))
        return render_template("review.html", employment=employment)

    @app.get("/staff/statistics")
    @role_required("staff")
    def statistics():
        counts = {s: Employment.query.filter_by(status=s).count() for s in ("pending", "approved", "rejected")}
        counts["total"] = sum(counts.values())
        grouped = db.session.query(Employment.employer_type, func.count(Employment.id)).filter_by(status="approved").group_by(Employment.employer_type).all()
        return render_template("statistics.html", counts=counts, employer_type_stats=grouped)

    @app.cli.command("init-demo")
    def init_demo_command():
        init_demo_data(); click.echo("演示数据初始化完成")

    with app.app_context():
        db.create_all()
    return app


def init_demo_data():
    if User.query.filter_by(username="student001").first(): return
    graduate = Graduate(student_no="2026001", name="张三", major="计算机科学与技术", class_name="计科2201班", phone="13800000000")
    student = User(username="student001", role="student", graduate=graduate); student.set_password("123456")
    staff = User(username="admin", role="staff"); staff.set_password("admin123")
    db.session.add_all([student, staff]); db.session.commit()


app = create_app()

if __name__ == "__main__":
    with app.app_context(): init_demo_data()
    # 监听局域网网卡，便于同一 Wi-Fi 下的设备访问演示系统。
    app.run(host="0.0.0.0", port=5000, debug=True)
