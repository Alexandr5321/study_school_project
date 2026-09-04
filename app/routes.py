from flask import Blueprint, jsonify, request, session, render_template, redirect
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db


bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/about")
def about_page():
    return render_template("about.html")


@bp.get("/health/db")
def health_db():
    conn = get_db()

    with conn.cursor() as cur:
        cur.execute("SELECT 1 AS ok")
        row = cur.fetchone()

    return jsonify(database=row["ok"] == 1)


@bp.get("/register")
def register_page():
    return render_template("register.html")


@bp.post("/register")
def register():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")

    if not email or not password or not first_name:
        return jsonify(
            error="Email, password and first name are required"
        ), 400

    password_hash = generate_password_hash(password)

    conn = get_db()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (
                    email,
                    password_hash,
                    first_name,
                    last_name
                )
                VALUES (%s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    email,
                    password_hash,
                    first_name,
                    last_name,
                ),
            )

            user = cur.fetchone()

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify(error=str(e)), 400

    session["user_id"] = user["id"]

    return jsonify(
        message="Registration successful",
        user_id=user["id"],
    ), 201


@bp.get("/login")
def login_page():
    return render_template("login.html")


@bp.post("/login")
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify(
            error="Email and password are required"
        ), 400

    conn = get_db()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, password_hash, first_name, last_name
            FROM users
            WHERE email = %s
              AND is_active = TRUE;
            """,
            (email,),
        )

        user = cur.fetchone()

    if user is None:
        return jsonify(
            error="Invalid email or password"
        ), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify(
            error="Invalid email or password"
        ), 401

    session["user_id"] = user["id"]

    return jsonify(
        message="Login successful",
        user_id=user["id"],
    )


@bp.get("/session")
def get_session():
    user_id = session.get("user_id")

    if user_id is None:
        return jsonify(authenticated=False), 401

    conn = get_db()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, first_name, last_name
            FROM users
            WHERE id = %s
              AND is_active = TRUE;
            """,
            (user_id,),
        )

        user = cur.fetchone()

    if user is None:
        session.clear()
        return jsonify(authenticated=False), 401

    return jsonify(
        authenticated=True,
        user=user,
    )


@bp.post("/logout")
def logout():
    session.clear()

    return jsonify(
        message="Logout successful"
    )


@bp.get("/dashboard")
def dashboard():
    user_id = session.get("user_id")

    if user_id is None:
        return redirect("/login")

    conn = get_db()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, first_name, last_name
            FROM users
            WHERE id = %s
              AND is_active = TRUE;
            """,
            (user_id,),
        )

        user = cur.fetchone()

    if user is None:
        session.clear()
        return redirect("/login")

    return render_template(
        "dashboard.html",
        user=user,
    )


@bp.get("/lessons")
def lessons_page():
    return render_template("lessons.html")


@bp.get("/api/lessons")
def lessons_api():
    user_id = session.get("user_id")

    conn = get_db()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                lessons.id,
                lessons.title,
                lessons.description,
                lessons.start_at,
                lessons.zoom_link,
                CASE
                    WHEN lesson_enrollments.id IS NOT NULL
                    THEN TRUE
                    ELSE FALSE
                END AS enrolled
            FROM lessons
            LEFT JOIN lesson_enrollments
                ON lessons.id = lesson_enrollments.lesson_id
                AND lesson_enrollments.user_id = %s
            ORDER BY lessons.start_at;
            """,
            (user_id,),
        )

        lessons = cur.fetchall()

    for lesson in lessons:
        lesson["start_at"] = lesson["start_at"].strftime(
            "%d.%m.%Y %H:%M"
        )

    return jsonify(lessons=lessons)


@bp.post("/lessons/<int:lesson_id>/enroll")
def enroll_lesson(lesson_id):
    user_id = session.get("user_id")

    if user_id is None:
        return jsonify(error="Authentication required"), 401

    conn = get_db()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO lesson_enrollments (
                    user_id,
                    lesson_id
                )
                VALUES (%s, %s)
                ON CONFLICT (user_id, lesson_id)
                DO NOTHING
                RETURNING id;
                """,
                (user_id, lesson_id),
            )

            enrollment = cur.fetchone()

        conn.commit()

    except Exception as e:
        conn.rollback()
        return jsonify(error=str(e)), 400

    if enrollment is None:
        return jsonify(
            message="Already enrolled"
        )

    return jsonify(
        message="Successfully enrolled",
        enrollment_id=enrollment["id"],
    ), 201


@bp.get("/my-lessons")
def my_lessons():
    user_id = session.get("user_id")

    if user_id is None:
        return redirect("/login")

    conn = get_db()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                lessons.id,
                lessons.title,
                lessons.description,
                lessons.start_at,
                lessons.zoom_link
            FROM lessons
            JOIN lesson_enrollments
                ON lessons.id = lesson_enrollments.lesson_id
            WHERE lesson_enrollments.user_id = %s
            ORDER BY lessons.start_at;
            """,
            (user_id,),
        )

        lessons = cur.fetchall()

    for lesson in lessons:
        lesson["start_at"] = lesson["start_at"].strftime(
            "%d.%m.%Y %H:%M"
        )

    return jsonify(lessons=lessons)
