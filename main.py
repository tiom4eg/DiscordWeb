import bcrypt
from flask import *
from data import db_session
from data.user import User
from data.login import LoginForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user


app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


def main():
    db_session.global_init("db/data.db")
    app.run()


@app.route("/home")
def home():
    return render_template("main.html", title="Welcome!", text="home")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/home")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and form.password.data == str(user.password):
            login_user(user, remember=form.remember_me.data)
            return redirect("/home")
        return render_template('login.html',
                               message="Incorrect password or email",
                               form=form)
    return render_template('login.html', title='Authorization', form=form)


@app.route("/register")
def register():
    return render_template("main.html", title="Welcome!", text="register")


@app.route("/landing")
def landing():
    return render_template("main.html", title="Welcome!", text="landing")


@app.route("/commands")
def commands():
    return render_template("main.html", title="Welcome!", text="commands")


@app.route("/news")
def news():
    return render_template("main.html", title="Welcome!", text="news")


@app.route("/reviews")
def reviews():
    return render_template("main.html", title="Welcome!", text="reviews")


@app.route("/contacts")
def contacts():
    return render_template("main.html", title="Welcome!", text="contacts")


@app.route("/user_info")
def user_info():
    return render_template("main.html", title="Welcome!", text="user_info")


if __name__ == '__main__':
    main()