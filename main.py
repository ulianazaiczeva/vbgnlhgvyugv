from flask import Flask, render_template, redirect, jsonify, make_response, request, abort
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from loginform import LoginForm, JobsForm, RegisterForm, DepartmentForm
from data import db_session
from data.users import User
from data.jobs import Jobs
from data.departments import Departments
from data.hazard import Hazard
from flask_restful import Api
from data.jobs_resource import JobsResource, JobsListResource
from data.users_resource import UserResource, UsersListResource
import jobs_api
import users_api

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


def main():
    db_session.global_init("db/mars_explorer.sqlite")
    # app.register_blueprint(jobs_api.blueprint)  # Строчка для добавления REST-API из урока 1
    # app.register_blueprint(users_api.blueprint)
    # api.add_resource(JobsListResource, '/api/v2/jobs')
    # api.add_resource(JobsResource, '/api/v2/jobs/<int:job_id>')
    # api.add_resource(UsersListResource, '/api/v2/users')
    # api.add_resource(UserResource, '/api/v2/users/<int:user_id>')
    app.run()


@app.route('/')
@app.route('/index')
def index():
    session = db_session.create_session()
    jobs = session.query(Jobs)
    name, surname, category = [], [], []
    for job in jobs:
        for el in session.query(User).filter_by(id=job.team_leader):
            name.append(el.name)
            surname.append(el.surname)
        category.append(job.categories[0].id)
    return render_template("index.html", jobs=jobs, name=name, surname=surname, category=category)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/addjob', methods=['GET', 'POST'])
def addjob():
    form = JobsForm()
    if form.validate_on_submit():
        if form.validate_on_submit():
            session = db_session.create_session()
            job = Jobs()
            job.team_leader = form.team_leader.data
            job.job = form.job.data
            job.work_size = form.work_size.data
            job.collaborators = form.collaborators.data
            job.categories.append(session.query(Hazard).filter(Hazard.id == form.hazard.data).first())
            job.is_finished = form.is_finished.data
            session.add(job)
            session.commit()
            return redirect("/")
        return redirect('/logout')
    return render_template('addjob.html', title='Добавление работы', form=form)


@app.route('/jobs/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_job(id):
    form = JobsForm()
    if request.method == "GET":
        session = db_session.create_session()
        job = session.query(Jobs).filter(Jobs.id == id,
                                          (Jobs.team_leader == current_user.id)|(current_user.id == 1)).first()
        if job:
            form.team_leader.data = job.team_leader
            form.job.data = job.job
            form.work_size.data = job.work_size
            form.collaborators.data = job.collaborators
            form.hazard.data = job.categories[0].id
            form.is_finished.data = job.is_finished
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        job = session.query(Jobs).filter(Jobs.id == id,
                                          (Jobs.team_leader == current_user.id)|(current_user.id == 1)).first()
        if job:
            job.team_leader = form.team_leader.data
            job.job = form.job.data
            job.work_size = form.work_size.data
            job.collaborators = form.collaborators.data
            job.categories.remove(job.categories[0])
            job.categories.append(session.query(Hazard).filter(Hazard.id == form.hazard.data).first())
            job.is_finished = form.is_finished.data
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('addjob.html', title='Редактирование работы', form=form)


@app.route('/jobs_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def job_delete(id):
    session = db_session.create_session()
    job = session.query(Jobs).filter(Jobs.id == id,
                                      (Jobs.team_leader == current_user.id)|(current_user.id == 1)).first()
    if job:
        session.delete(job)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            surname=form.surname.data,
            email=form.email.data,
            hashed_password=form.password.data,
            age=form.age.data,
            speciality=form.speciality.data,
            address=form.address.data,
            position=form.position.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/departments')
@login_required
def departments():
    session = db_session.create_session()
    departments = session.query(Departments)
    name, surname = [], []
    for d in departments:
        for el in session.query(User).filter_by(id=d.chief):
            name.append(el.name)
            surname.append(el.surname)
    return render_template("departments.html", title='Департаменты', departments=departments, name=name, surname=surname)


@app.route('/adddepartment', methods=['GET', 'POST'])
@login_required
def adddepartment():
    form = DepartmentForm()
    if form.validate_on_submit():
        if form.validate_on_submit():
            session = db_session.create_session()
            d = Departments()
            d.title = form.title.data
            d.chief = form.chief.data
            d.members = form.members.data
            d.email = form.email.data
            session.add(d)
            session.commit()
            return redirect("/departments")
        return redirect('/logout')
    return render_template('adddepartment.html', title='Добавление департамента', form=form)


@app.route('/departments/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_department(id):
    form = DepartmentForm()
    if request.method == "GET":
        session = db_session.create_session()
        d = session.query(Departments).filter(Departments.id == id,
                                          (Departments.chief == current_user.id)|(current_user.id == 1)).first()
        if d:
            form.title.data = d.title
            form.chief.data = d.chief
            form.members.data = d.members
            form.email.data = d.email
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        d = session.query(Departments).filter(Departments.id == id,
                                          (Departments.chief == current_user.id)|(current_user.id == 1)).first()
        if d:
            d.title = form.title.data
            d.chief = form.chief.data
            d.members = form.members.data
            d.email = form.email.data
            session.commit()
            return redirect('/departments')
        else:
            abort(404)
    return render_template('adddepartment.html', title='Редактирование департаментов', form=form)


@app.route('/departments_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def department_delete(id):
    session = db_session.create_session()
    d = session.query(Departments).filter(Departments.id == id,
                                          (Departments.chief == current_user.id) | (current_user.id == 1)).first()
    if d:
        session.delete(d)
        session.commit()
    else:
        abort(404)
    return redirect('/departments')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    main()
