from functools import wraps

from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db


bp = Blueprint("main", __name__)


def get_user_role(user_id):
    conn = get_db()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                EXISTS (
                    SELECT 1
                    FROM students
                    WHERE user_id = %s
                ) AS is_student,
                EXISTS (
                    SELECT 1
                    FROM teachers
                    WHERE user_id = %s
                ) AS is_teacher;
            """,
            (user_id, user_id),
        )

        result = cur.fetchone()

    if result["is_student"]:
        return "student"

    if result["is_teacher"]:
        return "teacher"

    return None


def student_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")

        if user_id is None:
            return jsonify(error="Authentication required"), 401

        if get_user_role(user_id) != "student":
            return jsonify(error="Student access required"), 403

        return view(*args, **kwargs)

    return wrapped


def teacher_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")

        if user_id is None:
            return jsonify(error="Authentication required"), 401

        if get_user_role(user_id) != "teacher":
            return jsonify(error="Teacher access required"), 403

        return view(*args, **kwargs)

    return wrapped


@bp.get("/")
def index():
    return jsonify(status="ok")


@bp.get("/health/db")
def health_db():
    conn = get_db()

    with conn.cursor() as cur:
        cur.execute("SELECT 1 AS ok")
        row = cur.fetchone()

    return jsonify(database=row["ok"] == 1)


@bp.post("/register")
def register():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    role = data.get("role")

    if not email or not password or not first_name or not role:
        return jsonify(error="Missing required fields"), 400

    if role not in ("student", "teacher"):
        return jsonify(error="Invalid role"), 400

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
            user_id = user["id"]

            if role == "student":
                cur.execute(
                    """
                    INSERT INTO students (user_id)
                    VALUES (%s);
                    """,
                    (user_id,),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO teachers (user_id)
                    VALUES (%s);
                    """,
                    (user_id,),
                )

        conn.commit()

    except Exception:
        conn.rollback()
        return jsonify(error="Registration failed"), 400

    return jsonify(
        message="User registered",
        user_id=user_id,
        role=role,
    ), 201


@bp.post("/login")
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify(error="Email and password are required"), 400

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
        return jsonify(error="Invalid email or password"), 401

    if not check_password_hash(user["password_hash"], password):
        return jsonify(error="Invalid email or password"), 401

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

    role = get_user_role(user["id"])

    if role is None:
        session.clear()
        return jsonify(error="User has no valid role"), 403

    return jsonify(
        authenticated=True,
        user=user,
        role=role,
    )


@bp.post("/logout")
def logout():
    session.clear()

    return jsonify(
        message="Logout successful"
    )


@bp.get("/student/test")
@student_required
def student_test():
    return jsonify(
        message="Hello student"
    )


@bp.get("/teacher/test")
@teacher_required
def teacher_test():
    return jsonify(
        message="Hello teacher"
    )
