import pytest
from cwk import app, db, intersection
from sqlalchemy.sql import func, desc
from db_schema import User, Expense, Project, UserProjectRelation, AHPWeights, ProjectMilestone, ProjectTechnology, Technology
from werkzeug.security import generate_password_hash, check_password_hash
import numpy as np
import json
import datetime
import requests
from bs4 import BeautifulSoup

@pytest.fixture
def test_client():
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///database.sqlite"
    app.config['TESTING'] = True
    
    with app.test_client() as test_client:
        with app.app_context():
            db.create_all()
        yield test_client
        with app.app_context():
            db.drop_all()

@pytest.fixture
def logged_in_user(test_client):
    with app.app_context():
        user = User("Mike18", generate_password_hash("password"), "Michael", "Cooper", "michael@tedxwarwick.com", "07732444444", 1, "en", "GMT+0", "£", True, 7)
        db.session.add(user)

        project = Project("Project A", 1, 100000, datetime.datetime.now().date(), datetime.datetime.now().date(), 1, False, "www.github.com", "abcdefghijklmnop")
        db.session.add(project)

        relation = UserProjectRelation(1, 1, False, "Project Manager")
        db.session.add(relation)

        technologies = ["Python", "HTML", "SQLite", "SaaS", "Jinja", "AWS", "Azure"]
        technology_list = [Technology(x) for x in technologies]
        db.session.add_all(technology_list)

        db.session.commit()

        # Log in as the user
        response = test_client.post('/login', data={
            'username': 'Mike18',
            'password': 'password'
        })

        yield test_client

        db.session.delete(user)
       # db.session.commit()

def test_login():
    # Create a test client for the app
    with app.test_client() as client:
        # Send a POST request with a username and password to the login route
        response = client.post('/login', data={'username': 'Mike18', 'password': 'password'})
        # Verify that the response is a redirect to the dashboard page
        assert response.status_code == 302 # conveys login was successful
        assert response.location == 'http://localhost/' # accessed homepage

def test_user_registration(test_client):
    # Send a POST request to register a new user
    response = test_client.post('/register', data={'username': 'testuser1', 'password': 'testpassword1', 'firstname': 'user1', 
                                                   'lastname':'last1', 'email': 'user1.last1@warwick.com'})
    
    # Check that the response status code is 302 (redirect) and user is redirected to homepage
    assert response.status_code == 302
    assert response.location == 'http://localhost/'
    
    # Retrieve the user data from the database
    user = User.query.filter_by(username='testuser1').first()

    # Check that the user data matches the data entered in the user input form
    assert user.username == 'testuser1'
    assert check_password_hash(user.password, 'testpassword1')


def test_specific_user_expenses(logged_in_user, test_client):
    # Create a new user in the database
    with app.app_context():
        errors = 0

        ahpWeights = AHPWeights(np.array([1, 2, 4, 5, 6])) # to satisfy ahp_check dect
        db.session.add(ahpWeights)

        db.session.commit()

        # Submit expense data as the logged in user
        response = logged_in_user.post('/expenses/1', data={
            'expTitle': "myexpense2",
            'expDescription': 'Hey I made a new purchase today',
            'expAmount': 100,
            'expDate': '2002-04-04'
        })

        # Check that the response status code is 200 and the expenses were created
        expense = Expense.query.filter_by(name='myexpense2').first()
        if not (response.status_code == 200): 
            print("a")
            errors+=1
        if not (expense.project_id == 1): 
            print("b")
            errors+=1
        if not (expense.name == "myexpense2"): 
            print("c")
            errors+=1
        assert errors == 0


def test_specific_user_milestones(test_client, logged_in_user):
# Create a new user in the database
    with app.app_context():
        errors = 0
        ahpWeights = AHPWeights(np.array([1, 2, 4, 5, 6])) # to satisfy ahp_check dect
        db.session.add(ahpWeights)

        db.session.commit()

        # Submit expense data as the logged in user
        response = logged_in_user.post('/milestones/1', data={
            'milTitle': "mymilestone1",
            'milDescription': 'Hey I made a new milestone today',
            'milDate': '2003-04-24'
        })

        # Check that the response status code is 200 and the expenses were created
        milestone = ProjectMilestone.query.filter_by(title='mymilestone1').first()
        if not (response.status_code == 200): errors+=1
        if not (milestone.project_id == 1): errors+=1
        if not (milestone.title == "mymilestone1"): errors+=1
        print("So the title is "+milestone.title)
        assert errors == 0

def test_AHP_weightings(logged_in_user):
    matrix_one = [[1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1]]
    matrix_two = [[1, 3, 3, 3, 3, 3],
                  [0.3333333333333333, 1, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333],
                  [0.3333333333333333, 3, 1, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333],
                  [0.3333333333333333, 3, 3, 1, 0.3333333333333333, 0.3333333333333333],
                  [0.3333333333333333, 3, 3, 3, 1, 0.3333333333333333],
                  [0.3333333333333333, 3, 3, 3, 3, 1]]
    matrix_three = [[1, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333],
                    [3, 1, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333],
                    [3, 3, 1, 0.3333333333333333, 0.3333333333333333, 0.3333333333333333],
                    [3, 3, 3, 1, 0.3333333333333333, 0.3333333333333333],
                    [3, 3, 3, 3, 1, 0.3333333333333333],
                    [3, 3, 3, 3, 3, 1]]
    # Create a JSON object with a key "matrix" and a value that is a 2D array
    payload = {"matrix": matrix_three}
    
    # Convert the payload to a JSON string
    payload_string = json.dumps(payload)
    
    # Post the payload to the endpoint
    response = logged_in_user.post("/ahp_data", data=payload_string, content_type="application/json")
    assert response.status_code == 200

    weighting_array = AHPWeights.query.order_by(desc(AHPWeights.id)).first().weightings

    assert len(weighting_array) == 6
    for num in weighting_array: assert 0 <= num <= 1
    assert round(sum(weighting_array), 5) == 1

def test_tech_intersection(logged_in_user):
    pt1 = ProjectTechnology(1, 1)
    pt2 = ProjectTechnology(1, 2)
    pt3 = ProjectTechnology(1, 3)
    db.session.add_all([pt1, pt2, pt3])
    db.session.commit()

    url = "http://127.0.0.1:5123/project_technology/1"
    response = requests.get(url)
    html_content = response.content

    # Step 2: Parse the HTML content to extract the name attribute values of the checkbox input elements
    soup = BeautifulSoup(html_content, 'html.parser')
    checkbox_ids_to_select = ["1", "2", "3"]
    checkbox_names_to_select = []
    for checkbox_id in checkbox_ids_to_select:
        checkbox = soup.find('input', {'id': checkbox_id})
        if checkbox is None:
            raise ValueError(f"No checkbox with id {checkbox_id} found on the page")
        checkbox_names_to_select.append(checkbox['name'])

    # Step 3: Define the data dictionary to check the checkboxes
    data = {}
    for checkbox_name in checkbox_names_to_select:
        data[checkbox_name] = 'on'

    # Step 4: Send the POST request with the data dictionary
    response = logged_in_user.requests.post("/project_technology/1", data=data)



    # response1 = logged_in_user.post("/project_technology/1", data= {"id":1})
    # response2 = logged_in_user.post("/project_technology/1", data= {"id":2})
    # response3 = logged_in_user.post("/project_technology/1", data= {"id":3})
    # assert response1.status_code == 302
    # assert response2.status_code == 302
    # uresponse1 = logged_in_user.post("/user_technology", data= {"user_id": 1, "technology_id": 1, "years": 1})
    # assert uresponse1.status_code == 302

    # assert intersection(1) == 0
    



# # check the matrix is being received correctly - check on different types of matricies

# # test different branches of one or two routes (eg submitting(get and post) as a manager, employee)