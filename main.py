import bcrypt
from flask import *
from data.user import User
from data.salt import salt
from data import db_session
from datetime import datetime
from data.review import Review
from data.login import LoginForm
from data.register import Register
from data.add_review import Add_review
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
        if user and str(bcrypt.hashpw(str(form.password.data).encode(), salt)) == user.password:
            login_user(user, remember=form.remember_me.data)
            return redirect("/home")
        return render_template('login.html',
                               message="Incorrect password or email",
                               form=form)
    return render_template('login.html', title='Authorization', form=form)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = Register()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = User()
        user.nickname = form.nickname.data
        user.email = form.email.data
        user.password = str(bcrypt.hashpw(form.password.data.encode(), salt))
        if not db_sess.query(User).filter(User.nickname == form.nickname.data).first() is None:
        	return render_template("register.html", title="Registration", form=form, message="Current nickname is busy")
        if not db_sess.query(User).filter(User.email == form.email.data).first() is None:
        	return render_template("register.html", title="Registration", form=form, message="Current email is busy")
        if form.nickname.data == "":
            return render_template("register.html", title="Registration", form=form, message="You can't have an empty nick")
        if form.password.data == form.repeat_password.data:
            db_sess.add(user)
            db_sess.commit()
            login_user(user, remember=False)
            return redirect("/home")
        else:
            return render_template("register.html", title="Registration", form=form, message="Password mismatch")    	
    return render_template("register.html", title="Registration", form=form)


@app.route("/reviews")
def reviews():
    db_sess = db_session.create_session()
    reviews = db_sess.query(Review)
    users = db_sess.query(User)
    coll = {user.id: user.nickname for user in users}
    return render_template("review_log.html", title="Reviews", coll=coll, reviews=[elem for elem in reviews])


@app.route("/add_review", methods=['GET', 'POST'])
def add_review():
    review = Add_review()
    message = ""
    if review.validate_on_submit():
        db_sess = db_session.create_session()
        rev = Review()
        rev.author = current_user.id
        rev.date = datetime.now()
        rev.time = datetime.now()
        rev.content = request.form['text']
        if request.form['text'] != "":
            db_sess.add(rev)
            db_sess.commit()
            return redirect('/reviews')
        else:
            message = "Field is empty"
    return render_template("add_review.html", title="Write review", form=review, type="new", message=message)


@app.route('/edit_review/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_review(id):
    form = Add_review()
    db_sess = db_session.create_session()
    rev = db_sess.query(Review).filter(Review.id == id, 
                               (Review.author == current_user.id)).first()
    message = ""
    if request.method == "GET":
        if rev:
            return render_template("add_review.html", title="Edit review", form=form, content=rev.content, type="edit")
        else:
            abort(404)

    if form.validate_on_submit():
        if rev:
            if request.form['text'] != "":
                rev.content = request.form['text']
                db_sess.commit()
                return redirect('/reviews')
            else:
                message = "Field is empty"
        else:
            abort(404)
    return render_template("add_review.html", title="Edit review", form=form, type="edit", message=message)


@app.route('/delete_review/<int:id>', methods=['GET', 'POST'])
@login_required
def review_delete(id):
    db_sess = db_session.create_session()
    review = db_sess.query(Review).filter(Review.id == id, 
                                    (Review.author == current_user.id)).first()
    if review:
        db_sess.delete(review)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/reviews')


@app.route("/landing")
def landing():
    return render_template("main.html", title="Welcome!", text="landing")


@app.route("/commands")
def commands():
    return render_template("main.html", title="Welcome!", text="commands")


@app.route("/news")
def news():
    return render_template("main.html", title="Welcome!", text="news")


@app.route("/contacts")
def contacts():
    return render_template("main.html", title="Welcome!", text="contacts")


@app.route("/user_info")
def user_info():
    return render_template("main.html", title="Welcome!", text="user_info")


if __name__ == '__main__':
    main()