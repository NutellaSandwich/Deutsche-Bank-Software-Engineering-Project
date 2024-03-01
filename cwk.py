from aifc import Error
from xml.dom import NoModificationAllowedErr
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug import security
from werkzeug.utils import secure_filename
from markupsafe import escape
from flask import Flask, Response, make_response, render_template, render_template_string, request, redirect, flash, send_file, jsonify
from sqlalchemy import desc, JSON
from datetime import datetime, timedelta
import os 
import json
from datetime import datetime
from sqlalchemy.sql.expression import func
from dotenv import load_dotenv
from ml import ml # import ml code

import numpy as np

from code_metrics import super_lint

# -------------------------
app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")

# User file upload config
UPLOAD_FOLDER = "./static/images/uploads/profiles"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_UPLOAD_LENGTH"] = 4 * 1024 * 1024 # Set max file upload size to be 4 MB


# Database config and import
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///database.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
from db_schema import db, User, Department, UserTechnology, Technology, ProjectTechnology, Project, Expense, ProjectMilestone, TeamMemberSurvey, UserProjectRelation, Language, Timezone, Currency, AHPWeights, dbinit
db.init_app(app)

resetdb = True  # Change to True to reset the database with the data defined in the db_schema.py file.
if resetdb:
    with app.app_context():
        # Drop everything, create all tables and populate with data
        db.drop_all()
        db.create_all()
        dbinit()


# Import login manager
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "/login" # sets the route to go to if the user attempts to access a route which requries them to be logged in and they are not.

@login_manager.user_loader
def load_user(username):
    return User.query.get(username)

bypass_ahp = False # Change to true to bypass the AHP survey
# Decorator function to check if AHP survey has been completed - forcing the user to do it before anything else.
from functools import wraps
def ahp_check(func):
    @wraps(func)
    def decorated_func(*args, **kwargs):
        if bypass_ahp:
            return func(*args, **kwargs)        
        
        # Check if the AHP results are present in the AHPWeights table
        rows = AHPWeights.query.all()
        # print(rows)

        if len(rows) > 0: # AHP weights are present.
            # print("ahp weights present.")
            return func(*args, **kwargs )
        else: # No AHP weights present in database - make user add them.
            # print("no ahp weights")
            flash("Please complete the AHP survey before moving on!", "error")
            return redirect("/ahp")
    return decorated_func





# Routes
@app.route('/')
@login_required
@ahp_check
def index():
    return render_template('home.html')



@app.route("/register", methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        # already logged in
        return redirect("/")

    if request.method == "POST":
        # Get the form fields.
        username = escape(request.form.get("username"))
        password = escape(request.form.get("password"))
        passwordHash = security.generate_password_hash(password)
        firstname = escape(request.form.get("firstname"))
        lastname = escape(request.form.get("lastname"))
        email = escape(request.form.get("email"))

        # attempt to add new user to database
        try:
            newUser = User(username=username, password=passwordHash, firstname=firstname, lastname=lastname, email=email, phone_number=None, department_id=1, language=None, timezone=None, currency=None, working=True, yearsAtCompany=None)
            db.session.add(newUser)
            db.session.commit()

        except IntegrityError as exc:
            db.session.rollback()
            flash("Could not register user!", "error")
            print(exc)
            return redirect("/register")
        
        makeLogin(username, password) # Logs the user in with the details they provided
        return redirect("/")

    if request.method == "GET":
        return render_template("register.html")


# Function which takes in a plaintext username and password and attempts to log the user in. Checks if the entered password matches the hashed one in the database.
def makeLogin(username, password):
    try:
        # Get the user with the entered username
        dbUser = User.query.filter_by(username=username).first()
        if dbUser is None:
            flash("User doesn't exist.")
            return False
        
        if not security.check_password_hash(dbUser.password, password):
#             print("password doesn't match")
            flash("Invalid account details")
            return False

        # entered password matches the stored password for the user, login them in
        res = login_user(dbUser)
        return True

    except:
        return False


@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        # already logged in.
        return redirect("/")

    if request.method == "POST":
        # Get form fields.
        username = escape(request.form.get("username"))
        password = escape(request.form.get("password"))

        # Attempt to login
        if makeLogin(username, password):
            print("login successful")
            return redirect("/")
        else:
            flash("Unable to login", "error")
            return redirect("/login")
    
    if request.method == "GET":
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    # If a user is logged in, then log them out.
    if current_user.is_authenticated:
        logout_user()
    return redirect("/")

@app.route("/expenses/<project_id>", methods=["GET", "POST"])
@login_required
@ahp_check
def expenses(project_id):
    if request.method == "POST":
        title = escape(request.form.get("expTitle"))
        description = escape(request.form.get("expDescription"))
        amount = request.form.get("expAmount")
        date = request.form.get("expDate")
        try: 
            # check if project with id exists
            projects = db.session.query(Project).all()
            project_ids = [str(p.id) for p in projects]

            if project_id not in project_ids:
#                 print("Invalid project ID")
                flash("Invalid project ID")
                return redirect("/projects")


            userRole = UserProjectRelation.query.filter_by(user_id=current_user.id, project_id=int(project_id)).first().role

            # Check user is allowed to add expense
            if userRole.lower() in ["project manager", "business analyst"]:
                prev_expense_id = db.session.query(func.max(Expense.expense_id)).first()[0]
                if prev_expense_id == None: prev_expense_id = 0
                new_expense = Expense(project_id=int(project_id), expense_id=prev_expense_id+1, name=title, 
                description=description, amount=amount, timestamp=datetime.strptime(date, '%Y-%m-%d'))
                db.session.add(new_expense)
                db.session.commit()

            flash("Expense created!", category="success")
            ml()

            return redirect("/project/" + str(project_id))
        except Exception as e:
#             print(e)
            flash("Expense could not be created!", category="error")
            return redirect("/expenses/" + str(project_id))


    return render_template("expenses.html", project_id=project_id)


@app.route("/milestones/<project_id>", methods=["GET", "POST"])
@login_required
@ahp_check
def milestones(project_id):
    if request.method == "POST":
        title = escape(request.form.get("milTitle"))
        description = escape(request.form.get("milDescription"))
        date = request.form.get("milDate")
        try: 
            projects = db.session.query(Project).all()
            project_ids = [str(p.id) for p in projects]

            if project_id not in project_ids:
#                 print("Invalid project ID")
                flash("Invalid project ID")
                return redirect("/projects")
            
            userRole = UserProjectRelation.query.filter_by(user_id=current_user.id, project_id=int(project_id)).first().role
            if userRole.lower() in ["project manager", "business analyst"]:
                new_milestone = ProjectMilestone(project_id=project_id, title=title,description=description,
                deadline=datetime.strptime(date, '%Y-%m-%d'), completed_date=None )
                db.session.add(new_milestone)
                db.session.commit()
            
            flash("Milestone created!", category="success")
            ml()

            return redirect("/project/" + str(project_id))
        except Exception as e:
#             print(e)
            flash("Milestone could not be created!", category="error")
            return redirect("/milestones/" + str(project_id))
        
    return render_template("milestones.html", project_id=project_id)


@app.route("/ahp", methods=["GET", "POST"])
@login_required
def ahp():
    return render_template("ahp.html")


@app.route("/ahp_data", methods=["POST"])
def ahp_data():
    if request.method == "POST":
  
        matrix = request.get_json()["matrix"]
        if matrix != None: it = iter(matrix)
        # Check matrix is valid
        if matrix == None or len(matrix)!=6 and (not all(len(l) == 6 for l in it)):
            result = {'message': 'Error submitted is invalid.'}
            response = make_response(jsonify(result), 400)  
        else:
            try:
                # Convert the matrix of AHP results into a list and add to database.
                eigenvalues, eigenvectors = np.linalg.eig(matrix)
                max_index = np.argmax(eigenvalues)
                priority_vector = eigenvectors[:, max_index]
                weights = priority_vector.real / np.sum(priority_vector.real)
                new_weight = AHPWeights(weightings=weights)
                db.session.add(new_weight)
                db.session.commit()
#                 print("data inserted")
                result = {'message': 'Data inserted successfully'}
                response = make_response(jsonify(result), 200)
                return response
            except Exception as e:
#                 print(e)
#                 print("DATA NOT INSERTED")
                result = {'message': 'Data not inserted successfully'}
                response = make_response(jsonify(result), 400)  
                return response

        return response


@app.route("/profile")
@login_required
@ahp_check
def profile():
    # Gets user profile page info
    if request.method == "GET":

        user_department_id = User.query.get(current_user.id).department_id
        user_department = Department.query.get(user_department_id)
        
        user_projects = db.session.query(Project).join(UserProjectRelation)\
            .filter(Project.id == UserProjectRelation.project_id, UserProjectRelation.user_id == current_user.id).all()
        # print("projects: " + str(user_projects1))


        return render_template("profile.html", user_department=user_department, user_projects=user_projects)


@app.route("/edit_profile", methods=["POST", "GET"])
@login_required
@ahp_check
def edit_profile(): 
    if request.method == "POST":
        # Handle updating of user details.
        username = escape(request.form.get("username"))
        new_firstname = escape(request.form.get("firstname"))
        new_lastname = escape(request.form.get("lastname"))
        new_email = escape(request.form.get("email"))
        new_phone_number = escape(request.form.get("phone_number"))
        new_department_id = escape(request.form.get("department"))
        new_language = escape(request.form.get("language"))
        new_timezone = escape(request.form.get("timezone"))
        new_currency = escape(request.form.get("currency"))
        new_working = escape(request.form.get("working"))
        new_years_at_company = escape(request.form.get("years_at_company"))

        # Check user with the same email doesn't already exist.
        user_email_test = db.session.query(User).filter(User.email == new_email).first()
        if user_email_test is not None and current_user.email != new_email:
            # Email already exists in database.
#             print("email already exists in database")
            flash("New email already in use", "error")
            return redirect("/profile")
    

        user_data =  db.session.query(User).filter(User.username == current_user.username).first()
        if user_data is None:
#             print("error, user doesn't exist")
            flash("Unable to update details", "error")
            return redirect("/profile")

        # Update user_data values in the database
        try:
            user_data.firstname = new_firstname
            user_data.lastname = new_lastname
            user_data.email = new_email
            user_data.phone_number = new_phone_number
            user_data.department_id = new_department_id
            user_data.language = new_language
            user_data.timezone = new_timezone
            user_data.currency = new_currency
            user_data.working = True if new_working == "True" else False
            user_data.yearsAtCompany = new_years_at_company

            
            db.session.commit()
        except Exception as e:
#             print(e)
#             print("error updating user")
            flash("Unable to update details", "error")
            return redirect("/profile")

        # ----- Getting user profile image -----
        # Check image file has been submitted
        if "image_file" not in request.files:
            flash("No file submitted", "error")
            return redirect("/profile")
        
        image_file = request.files["image_file"]

        # Addition checks user has selected a file.
        if not image_file or image_file.filename == "":
            # flash("No file submitted", "error")
            return redirect("/profile")
        
        # Check file extension
        if "." not in image_file.filename:
            flash("Invalid file uploaded", "error")
            return redirect(request.url)
        file_extension = image_file.filename.rsplit(".", 1)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            flash("Invalid file uploaded", "error")
            return redirect("/profile")
        
        # Make filename the users username plus appropriate extension
        # Overwrites file if already exists.
        filename = secure_filename(current_user.username + "." + file_extension)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(filepath)

        # Insert file path into User table in database
        user_data.profile_image_path = filepath
        db.session.commit()
        
        flash("User details updated", "message")
        return redirect("/profile")

    elif request.method == "GET":
        departments = db.session.query(Department).all()
        languages = db.session.query(Language).all()
        timezones = db.session.query(Timezone).all()
        currencies = db.session.query(Currency).all()

        return render_template("edit_profile.html", departments=departments, languages=languages, timezones=timezones, currencies=currencies)


@app.route("/add_technology", methods=["POST", "GET"])
@login_required
@ahp_check
def add_technology():
    if request.method == "POST":
        technology = escape(request.form.get("technology"))

        # Check if technology already exists in database
        exists = db.session.query(Technology).filter(Technology.name == technology).first()
        if exists is not None:
#             print("Technology already exists in the database")
            flash("Technology already exists", "message")
            return redirect(request.referrer)

        # Add new technology to database
        try:
            new_technology = Technology(technology)
            db.session.add(new_technology)
            db.session.commit()
            flash("Technology added", "message")
        except:
#             print("Error, unable to add technology")
            flash("Unable to add technology", "error")
            return redirect(request.referrer)

        return redirect(request.referrer)
    elif request.method == "GET":

        return render_template("add_technology.html")

@app.route("/user_technology", methods=["POST", "GET"])
@login_required
@ahp_check
def user_technology():
    if request.method == "POST":
        technologies = db.session.query(Technology).all()
        years = [[tech.id, tech.name, request.form.get(str(tech.id))] for tech in technologies]
        
        try:
            # loop through zip of technologies and collected years experience
            for entry in years:
                id = entry[0]
                name = entry[1]
                years_exp = entry[2]

                # Get row from database
                row = db.session.query(UserTechnology).filter(UserTechnology.user_id==current_user.id, UserTechnology.technology_id==id).first()
                if row is not None: # if row exists, update years value.
                    # print("Row for " + name + " exists, updating value")
                    row.yearsExperience = years_exp

                else: # if row doesnt exist, create and insert
                    # print("Row for " + name + " doesn't exist, creating row")
                    new_row = UserTechnology(current_user.id, id, years_exp)
                    db.session.add(new_row)

            db.session.commit()
        except:
#             print("error - user tech")
            flash("Unable to update technologies", "error")
            return redirect("/profile")

#         print("user technologies updated")
        flash("Technologies updated", "message")
        ml()
        return redirect("/profile")
    
    elif request.method == "GET":
        user_id = current_user.id
        technologies = db.session.query(Technology).all()
        
        technology_list = []
        for technology in technologies:
            row  = db.session.query(UserTechnology).filter(UserTechnology.user_id == user_id, UserTechnology.technology_id == technology.id).first()
            # print(row)

            years_experience = row.yearsExperience if row else 0

            tech_info = {"technology_id": technology.id, "name": technology.name, "years": years_experience}
            technology_list.append(tech_info)
        
        # print(technology_list)

        return render_template("user_technology.html", technologies = technology_list)


@app.route("/survey/<project_id>", methods=["GET","POST"])
@login_required
@ahp_check
def survey(project_id):
    try:
        projects = db.session.query(Project).all()
        project_ids = [str(p.id) for p in projects]

        if project_id not in project_ids:
#             print("Invalid project ID")
            flash("Invalid project ID")
            return redirect("/survey/" + str(project_id))
        
        this_monday = datetime.utcnow().date() - timedelta(days=datetime.utcnow().date().weekday())
        next_monday = this_monday + timedelta(weeks=1)

        existing_survey = TeamMemberSurvey.query.filter_by(user_id=current_user.id, project_id=project_id).filter(TeamMemberSurvey.timestamp >= this_monday).first()
#         print(existing_survey)
        if request.method == "POST":
            # Get form fields
            experience = escape(request.form.get("experience"))
            working_environment = escape(request.form.get("working_environment"))
            hours_worked = escape(request.form.get("hours_worked"))
            communication = escape(request.form.get("communication"))

            # Store survey results in database 
            new_survey = TeamMemberSurvey(current_user.id, project_id=project_id, experience=str(experience), working_environment=str(working_environment), hours_worked=str(hours_worked), communication=str(communication),timestamp=datetime.utcnow())        
            db.session.add(new_survey)
            db.session.commit()
            ml()

            return redirect("/project/"+project_id)

    except Exception as e:
#         print(e)
        return redirect("/projects")
  #  return render_template('survey.html', project_id=project_id)
    
    if existing_survey:
        return render_template("survey_not_available.html", next_monday=next_monday)
    else:
        return render_template('survey.html', project_id=project_id)
    

@app.route("/projects", methods=["GET"])
@login_required
@ahp_check
def projects():
    if request.method == "GET":
        # Get user projects
        user_projects = db.session.query(Project).join(UserProjectRelation)\
            .filter(Project.id == UserProjectRelation.project_id, UserProjectRelation.user_id == current_user.id)\
            .order_by(Project.deadline).all()
        
        # Get manager info for each associated project.
        managers_db = db.session.query(User, Project).join(Project)\
            .filter(User.id == Project.manager_id).all()
        
        managers = {}
        for user, project in managers_db:
            managers[str(project.id)] = user.username

        return render_template("projects.html", user_projects=user_projects, managers=managers)

@app.route("/new_project", methods=["GET", "POST"])
@login_required
@ahp_check
def new_project():
    if request.method == "POST":
        # Get form fields
        name = escape(request.form.get("name"))
        budget = request.form.get("budget")
        start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d")
        deadline = datetime.strptime(request.form.get("deadline"), "%Y-%m-%d")
        #print(start_date)
        #print(deadline)
        is_complete = True if request.form.get("is_complete") == "True" else False
        scope = request.form.get("scope")
        repo_url = request.form.get("github_repo")
        repo_access_token = request.form.get("gh_repo_token")

        # create new project in database
        try:
            new_project = Project(name, current_user.id, budget, start_date, deadline, scope, is_complete, repo_url, repo_access_token)
            db.session.add(new_project)
            db.session.commit()

            # Add user project relation for the manager
            projectManagerRelation = UserProjectRelation(current_user.id, new_project.id, True, "Project Manager")
            db.session.add(projectManagerRelation)
            db.session.commit()
        except Exception as e:
#             print("Error creating project")
#             print(e)
            flash("Unable to create project", "error")
            return redirect("/projects")

        # Project successfully created.
#         print("Project created")
        flash("Project created", "message")
        return redirect("/projects")
    
    elif request.method == "GET":

        return render_template("new_project.html")


@app.route("/project/<id>", methods=["GET"])
@login_required
@ahp_check
def project(id):
    # Get details and check user is authorised to view project.
    project_details = db.session.query(Project).filter(Project.id == id).first()
    allowed_users = db.session.query(UserProjectRelation).filter(UserProjectRelation.project_id == project_details.id).all()
    allowed_user_id = [row.user_id for row in allowed_users]

    if current_user.id not in allowed_user_id:
#         print("User not authorise to view this project.")
        flash("User not authorised to view this project", "message")
        return redirect("/projects")



    project_surveys = db.session.query(TeamMemberSurvey).filter(TeamMemberSurvey.project_id==id).all()
    if len(project_surveys) < 1:
        flash("Please complete the user survey to get a prediction of success.", "message")


    
    is_manager = True if current_user.id == project_details.manager_id else False

    project_manager = User.query.get(project_details.manager_id)
    project_members = db.session.query(User, UserProjectRelation.role).join(UserProjectRelation).filter(User.id == UserProjectRelation.user_id, UserProjectRelation.project_id == id).all()

    project_technologies = db.session.query(Technology).join(ProjectTechnology).filter(Technology.id == ProjectTechnology.technology_id, ProjectTechnology.project_id == id).all()

    project_milestones = db.session.query(ProjectMilestone).filter(ProjectMilestone.project_id==id).all()

    code_quality = super_lint(project_details.repo_url, project_details.repo_token) * 100

    # render different templates/pass diff data depending on role.
    if is_manager:
        project_expenses = db.session.query(Expense).filter(Expense.project_id==id).order_by(desc(Expense.timestamp)).all()
        
        # Get project suggestions and check they aren't None.
        project_suggestions = db.session.query(Project.s1, Project.s2, Project.s3).filter(Project.id==id).first()
        if None in project_suggestions:
            project_suggestions = None

        return render_template("project.html", project=project_details, project_members=project_members, project_technologies=project_technologies, project_expenses=project_expenses, project_suggestions=project_suggestions, project_milestones=project_milestones, project_manager=project_manager, code_quality=code_quality)
    
    else:
        return render_template("user_project.html", project=project_details, project_members=project_members, project_technologies=project_technologies, project_milestones=project_milestones, project_manager=project_manager, code_quality=code_quality)


@app.route("/project_technology/<project_id>", methods=["GET", "POST"])
@login_required
@ahp_check
def project_technology(project_id):
    # check project ID exists.
    projects = db.session.query(Project).all()
    project_ids = [str(p.id) for p in projects]

    if project_id not in project_ids:
#         print("Invalid project ID")
        flash("Invalid project ID")
        return redirect("/projects")
    
    # Check user is PM for the given project
    project_details = db.session.query(Project).filter(Project.id == int(project_id)).first()
    is_manager = True if current_user.id == project_details.manager_id else False
    if not is_manager:
#         print("User not authorised to add technologies for this project")
        flash("User not authorised to add technologies for this project", "message")
        return redirect("/projects")

    if request.method == "POST":
        # Get list of technologies checked and store them in database.
        technologies = db.session.query(Technology).all()
        technology_list = [{"id": tech.id, "is_used": request.form.get(str(tech.id))} for tech in technologies]
        # print(technology_list)

        for tech in technology_list:
            # check if entry exists in database for this project-tech pair
            row = db.session.query(ProjectTechnology).filter(ProjectTechnology.technology_id == tech["id"], ProjectTechnology.project_id == project_id).first()

            if row is None: # Entry doesn't already exist. Add entry if tech.is_used is "True"
                if tech["is_used"] == "True":
                    new_row = ProjectTechnology(project_id, tech["id"])
                    db.session.add(new_row)
            elif row is not None: # Entry already exists, remove if tech.is_used is "False"
                if tech["is_used"] == None:
                    db.session.delete(row)
            
        db.session.commit()
      #  print(intersection(project_id))
        ml()

        return redirect("/project/" + project_id)

    elif request.method == "GET":
        # Get list of all technologies and whether they are used in the projected or not.
        technologies = db.session.query(Technology).all()

        technology_list = []
        for technology in technologies:
            row = db.session.query(ProjectTechnology).filter(ProjectTechnology.project_id == project_id, ProjectTechnology.technology_id == technology.id).first()

            is_used = True if row is not None else False
            tech_data = {"id": technology.id, "name": technology.name, "is_used": is_used}
            technology_list.append(tech_data)
            
#         print(technology_list)
        return render_template("project_technology.html", project = project_details, technologies = technology_list)


@app.route("/add_user/<project_id>", methods=["GET", "POST"])
@login_required
@ahp_check
def project_users(project_id):
    # check project ID exists
    projects = db.session.query(Project).all()
    project_ids = [str(p.id) for p in projects]

    if project_id not in project_ids:
#         print("Invalid project ID")
        flash("Invalid project ID", "message")
        return redirect("/projects")

    # Check if user is PM for the given project
    project_details = db.session.query(Project).filter(Project.id == int(project_id)).first()
    is_manager = True if current_user.id == project_details.manager_id else False
    if not is_manager:
#         print("User not authorised to add users to this project")
        flash("User not authorised to add users to this project", "message")
        return redirect("/projects")

    if request.method == "POST":
        # Get username and details entered in form, add UPR entry for them.
        new_username = escape(request.form.get("username"))
        new_role = escape(request.form.get("role"))

        # Check username exists.
        user_details = db.session.query(User).filter(User.username == new_username).first()
        if user_details is None:
#             print("User doesn't exist")
            flash("User doesn't exist", "message")
            return redirect("/add_user/" + project_id)
        
        # Create new UserProjectRelation entry for the new user
        new_entry = UserProjectRelation(user_details.id, project_id, False, new_role)
        db.session.add(new_entry)
        db.session.commit()
#         print("User added to project")
        flash("User added to project", "message")
        ml()

        return redirect("/project/" + project_id)
    
    elif request.method == "GET":
        return render_template("project_users.html", project=project_details)


@app.route("/edit_project/<project_id>", methods=["GET", "POST"])
@login_required
@ahp_check
def edit_project(project_id):
    # Check project with given id exists.
    project_details = db.session.query(Project).filter(Project.id == int(project_id)).first()
    if project_details is None:
#         print("Project with given ID doesn't exist")
        flash("Project with given ID doesn't exist", "error")
        return redirect("/projects")

    # Check user is PM for the project
    is_manager = True if current_user.id == project_details.manager_id else False
    if not is_manager:
#         print("User not authorised to edit details for this project")
        flash("User not authorised to edit details for this project", "error")
        return redirect("/projects")
    
    project_manager = User.query.get(project_details.manager_id)

    if request.method == "POST":
        # get all submitted form details
        new_name = escape(request.form.get("name"))
        new_budget = request.form.get("budget")
        new_start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d")
        new_deadline = datetime.strptime(request.form.get("deadline"), "%Y-%m-%d")
        new_is_complete = True if request.form.get("is_complete") == "True" else False
        new_scope = request.form.get("scope")
        new_repo_url = escape(request.form.get("github_repo"))
        new_repo_token = escape(request.form.get("gh_repo_token"))

        # Check the project exists
        check_project = Project.query.get(project_details.id)
        if check_project is None:
#             print("Error, project doesn't exist")
            flash("Project doesn't exist", "error")
            return redirect("/projects")
        
        # Try update the values
        try:
            project_details.name = new_name
            project_details.budget = new_budget
            project_details.start_date = new_start_date
            project_details.deadline = new_deadline
            project_details.is_completed = new_is_complete
            project_details.scope = new_scope
            project_details.repo_url = new_repo_url
            project_details.repo_token = new_repo_token

            db.session.commit()

            ml()

        except Exception as e:
#             print("Error updating project details")
            flash("Error updating project details", "error")
#             print(e)
            return redirect("/projects")

        return redirect("/project/" + project_id)
    elif request.method == "GET":    
        return render_template("edit_project.html", project=project_details, project_manager=project_manager)


@app.route("/leave_project/<project_id>", methods=["GET"])
@login_required
@ahp_check
def leave_project(project_id):
    if request.method == "GET":
        # Check project exists.
        project_details = Project.query.get(project_id)
        if project_details is None:
#             print("Project doesn't exist")
            flash("Project doesn't exist", "error") 
            return redirect("/projects")

        # Check user is a part of the project.
        rows = db.session.query(UserProjectRelation).filter(UserProjectRelation.project_id==project_id).all()
        user_ids = [row.user_id for row in rows]
        if current_user.id not in user_ids:
#             print("User is not a member of the project")
            flash("Unable to leave - User is not a member of a project", "error")
            return redirect("/projects")

        # Check if user is the PM (PM can't leave a project)
        user_row = db.session.query(UserProjectRelation).filter(UserProjectRelation.project_id==project_id, UserProjectRelation.user_id==current_user.id).first()
        if project_details.manager_id == current_user.id or user_row.is_manager == True:
#             print("User is Project Manager - unable to leave.")
            flash("User is Project Manager - unable to leave.", "error")
            # print("manager ID: " + str(project_details.manager_id))
            # print("User ID: " + str(current_user.id))
            # print("is manager?: " + str(user_row.is_manager))
            return redirect("/project/" + project_id)

        # Remove entry in UserProjectRelation
        try:
            db.session.delete(user_row)
            db.session.commit()
            ml()
        except Exception as e:
#             print("Unable to remove user from project")
            flash("Unable to remove user from project.", "error")
            return redirect("/projects")

        # Redirect to projects
        return redirect("/projects")
    
    
