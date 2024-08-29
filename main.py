from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)


app = Flask(__name__)
app.secret_key = "dklfasldfjoeieerTjof8sd7f"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class Todo(db.Model):
    __tablename__ = "todo list"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    desc: Mapped[str] = mapped_column()
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"))
    user = db.relationship("User", back_populates="todos")


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password=password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    todos = db.relationship("Todo", back_populates="user")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    if request.method == "POST":
        title = request.form["title"]
        desc = request.form["desc"]
        todo = Todo(title=title, desc=desc, user_id=current_user.id)
        db.session.add(todo)
        db.session.commit()
    todo = db.session.execute(
        db.select(Todo).filter_by(user_id=current_user.id).order_by(Todo.id)
    ).scalars()
    count = db.session.query(Todo).filter_by(user_id=current_user.id).count()

    return render_template("index.html", todo=todo, count=count, status=True)


@app.route("/delete/<int:id>")
@login_required
def delete(id):
    dtodo = db.get_or_404(Todo, id)
    db.session.delete(dtodo)
    db.session.commit()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = db.session.execute(
            db.select(User).filter((User.email == email) | (User.username == username))
        ).scalar_one_or_none()

        if existing_user:
            flash(
                "User already exists. Please login or choose a different username/email.",
                "danger",
            )
            return redirect(url_for("register"))

        new_user = User(username=username, email=email)
        new_user.set_password(password=password)
        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful! You can now login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db.session.execute(
            db.select(User).filter_by(email=email)
        ).scalar_one_or_none()

        if user and user.check_password(password):
            login_user(user)
            flash("Login Successful!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    return render_template("login.html")


@login_required
@app.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect("login")


if __name__ == "__main__":
    app.run(debug=True)
