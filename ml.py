import sqlite3
import json
import datetime
import numpy as np
from sklearn import svm
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from code_metrics import super_lint, lines_per_pull
from Success_calc import calculate_success_chance
from intersection import intersection
# from cwk import app


# ml project data
def get_ml_data():
  result = []
  conn = sqlite3.connect('database.sqlite')
  c = conn.cursor()

  # Retrieve data for each project from the database
  c.execute("SELECT id, scope, budget, start_date, deadline, repo_url, repo_token, is_completed, is_success FROM project")
  projects = c.fetchall()
  
  for project in projects:
    id = project[0]
    num_members = c.execute("SELECT COUNT(*) FROM user_project_relation WHERE project_id = ?", (id,)).fetchone()[0]
    exp_mean = c.execute("SELECT AVG(experience) FROM team_member_survey WHERE project_id = ?", (id,)).fetchone()[0]
    work_env_mean = c.execute("SELECT AVG(working_environment) FROM team_member_survey WHERE project_id = ?", (id,)).fetchone()[0]
    scope = project[1]
    budget = project[2]
    #print("\nMl:")
    #print(project[3])
    #print(project[4])

    start_date = datetime.datetime.strptime(project[3], '%Y-%m-%d').date()
    deadline = datetime.datetime.strptime(project[4], '%Y-%m-%d').date()
    time = (deadline - start_date).days
    hours_mean = c.execute("SELECT AVG(hours_worked) FROM team_member_survey WHERE project_id = ?", (id,)).fetchone()[0]
    comm = c.execute("SELECT AVG(communication) FROM team_member_survey WHERE project_id = ?", (id,)).fetchone()[0]
    r_url = project[5]
    r_token = project[6]
    is_c = project[7]
    is_s = project[8]
    result.append([id, num_members, exp_mean, work_env_mean, scope, budget, time, hours_mean, comm, r_url, r_token, bool(is_s), bool(is_c)])
  c.close()
  conn.close()
  return result

# get ahp weights
def get_weights():
  conn = sqlite3.connect('database.sqlite')
  cursor = conn.cursor()
  c = conn.execute("SELECT COUNT(*) FROM ahp_weights").fetchone()[0]
  if c == 0:
    cursor.close()
    conn.close()
    return None
  else:
    result = conn.execute("SELECT weightings FROM ahp_weights LIMIT 1").fetchone()[0]
    cursor.close()
    conn.close()
    return json.loads(result)


def save_c(c_value):
  conn = sqlite3.connect('database.sqlite')
  cursor = conn.cursor()
  st = 'UPDATE ml_c SET c = ?'
  cursor.execute(st, (c_value,))
  conn.commit()
  cursor.close()
  conn.close()

def get_c():
  conn = sqlite3.connect('database.sqlite')
  cursor = conn.cursor()
  c = conn.execute("SELECT c FROM ml_c LIMIT 1").fetchone()[0]
  #print(c)
  cursor.close()
  conn.close()
  if c == None:
    return 1.0
  return c

def out_to_db(out):
  if out: 
    conn = sqlite3.connect('database.sqlite')
    cursor = conn.cursor()

    st = 'UPDATE project SET pred = ?, accuracy = ?, s1 = ?, s2 = ?, s3 = ? WHERE id = ?'
    cursor.executemany(st, out)
    conn.commit()

    cursor.close()
    conn.close()

def low_acc(f, w, pid):
  out = []
  indexes = [1, 2, 3, 6, 7, 9]
  weights = [w[x] for x in indexes]
  for i in range(len(pid)):
    array = [f[i][j] for j in indexes]
    acc = calculate_success_chance(array, weights)
    out.append(("Success", acc, "Not enough training data", None, None, pid[i]))
  out_to_db(out)

def ml():
  #print("--------------ml call--------------------")

  # suggestion outputs
  features = [['Increase number of team members', 'Decrease number of team members'],
      ['Experience and expertise of team members below expectations', 'Experience and expertise of team members higher than needed'],
      ['Improve working environment'], #single
      ['Reduce scope', 'Widen scope'],
      ['Increase project budget', 'Decrease project budget'],
      ['Extend deadline', 'Shorten deadline'],
      ['Increase working hours per week', 'Decrease working hours per week'],
      ['Improve code quality'], #single
      ['Increase Github activity', 'Decrease Github activity'],
      ['Improve effectiveness of communication within team / with stakeholders'], #single
      ['Improve matching of technologies']] #single

  t = ['Failure', 'Success']
  
  # get ml inputs from database
  data = get_ml_data()
  if not data:
    return 0
  
  
  ### data syntax: 2d array
  ### 13 columns:
  ###
  ### project id 
  ### number of members
  ### mean experience of members
  ### mean of work environment score
  ### scope score
  ### budget 
  ### total time given to finish project 
  ### mean hours worked per week
  ### communication score
  ### repo url
  ### repo token
  ### is project successful (True/False)
  ### is project completed (True/False)
  ###

  # data array reconstruction
  repo = [row[9:11] for row in data]
  b = [row[-2:] for row in data]
  comm = [[row[8]] for row in data]
  data = [row[:8] for row in data]

  ## code quality
  cq = []
  for i in range(len(data)):
    cq.append([super_lint(str(repo[i][0]), str(repo[i][1]))])

  ## pull req per lines of code
  pr = []
  for i in range(len(data)):
    pr.append([lines_per_pull(str(repo[i][0]), str(repo[i][1]))])

  ## tech intersections
  tech = []
  for i in range(len(data)):
    tech.append([intersection(data[i][0])])

  ## stacking code quality, pull req per lines of code and comm
  data = np.hstack((data,cq,pr,comm,tech,b))

  ## split training and predict. ensure same columns as weights
  training_data = []
  predict_data = []
  for row in data:
    if row[-1]:
      training_data.append(row[:-1])
    else:
      predict_data.append(row[:-2]) # remove is_succesful as well
  

  p_id = [row[0] for row in predict_data] # get project id of data to predict
  predict_data = [row[1:] for row in predict_data]
  #print("predict data size: ", len(predict_data))

  # training data
  x = [row[1:-1] for row in training_data] # training data doesnt need id
  y = [int(row[-1]) for row in training_data] # is project successful (True/False)

  ### data syntax: 2d array
  ### 11 columns:
  ###
  ### number of members
  ### mean experience of members
  ### mean of work environment score
  ### scope score
  ### budget 
  ### total time given to finish project 
  ### mean hours worked per week
  ### code quality
  ### pull req per lines of code
  ### communication score
  ### tech intersection
  ###

  # get weights from database
  # has same column ordering as data
  weights = [0]*11
  weights_groups = get_weights()
  if weights_groups != None:
     if len(weights_groups) == 6:
       weights[0] = weights_groups[0]/2
       weights[1] = weights_groups[0]/2
       weights[2] = weights_groups[1]/2
       weights[3] = weights_groups[1]/2
       weights[4] = weights_groups[2]
       weights[5] = weights_groups[3]/2
       weights[6] = weights_groups[3]/2
       weights[7] = weights_groups[4]/2
       weights[8] = weights_groups[4]/2
       weights[9] = weights_groups[5]

  if len(x) < 2:
     # use other method
     low_acc(predict_data, weights, p_id)
     return 0

  #print("weights: ", weights)

  # get C value from database
  C = get_c()
  #print("old C: ", C)

  # prepare data 
  ## scaling data
  x_mean = [sum(c) / len(c) for c in zip(*x)] # scaling values closer to mean by weight
  for i, col in enumerate(zip(*x)):
    w = weights[i]
    m = x_mean[i]
    for j, value in enumerate(col):
      x[j][i] = (1-w) * value + w * m


  ## split data into training and testing sets from training_data
  x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2)#, random_state=1) # seed (random state) set to 1

  if len(set(y_train)) == 1:
    out = []
    for j in range(len(predict_data)):
      acc = calculate_success_chance(predict_data[j], weights)
      out.append(("Success", acc,"Data is too one sided, unable to train",None,None, p_id[j])) ##### change if solution written
    out_to_db(out)
    #print("training data one sided")
    return 0


  # SVM training

  clf = None # declare classifier
  clf_accuracy = 0 # classifier accuracy
  #print("svm training")
  ## find best c
  if len(x_train) < 50:
    f = 10*(0.11)**(len(x_train)/50) # c factor
    c_vals = [C/f/f,C/f,C,C*f,C*f*f]
    # Train a separate SVM model for each value of C
    models = []
    for c in c_vals:
        model = svm.SVC(kernel='rbf', C=c, gamma='scale')
        model.fit(x_train, y_train)
        models.append(model)

    # Evaluate the models on the test data
    accuracy = []
    for model in models:
        y_pred = model.predict(x_test)
        accuracy.append(accuracy_score(y_test, y_pred))
        #print(model.C, accuracy[-1])
    if len(set(accuracy)) == 1:
      clf_accuracy = accuracy[0]
      clf = models[2]
    else:
      ind = accuracy.index(max(accuracy)) 
      clf_accuracy = accuracy[ind]
      clf = models[ind]
    C = clf.C
  else:
    # create an SVM classifier
    clf = svm.SVC(kernel='rbf', gamma='scale', C=C)

    # train the classifier on the training data
    clf.fit(x_train, y_train)

    # calculate the accuracy of the model
    y_pred = clf.predict(x_test)
    clf_accuracy = accuracy_score(y_test, y_pred)
  acc_formatted = '{:.1f}'.format(clf_accuracy*100)

  # update C value in file
  if C == None:
    C = 1
  save_c(C)
  #print(len(x), " new C: ", C, " accuracy: ", clf_accuracy)

  if not predict_data:
    #print("nth to predict")
    return 0

  #### model chosen ####

  # decision: ml prediction or not
  out = [] # output array
  #print("accuracy: ", clf_accuracy)
  if clf_accuracy > 0.6: ## only use ml output if accuracy higher than 60%
    # get index of support vectors of class 1 
    # ( 1 for project success, 0 for project failure )
    # get feature values (x) of support vectors of class 1
    sv = clf.support_vectors_[clf.dual_coef_[0] > 0]
    f = np.mean(sv, axis=0) # to compare with, determine suggestions

    # make prediction
    pj_pred = clf.predict(predict_data)
 
    # out array syntax: (prediction, accuracy, feature 1, feature 2, feature 3) all varchar
    for j in range(len(predict_data)):
      x_comp = f - predict_data[j]
      x_comp = x_comp.tolist()
      if x_comp[10] < 0:
        x_comp[10] = 0 # remove: "reduce tech"
      if x_comp[9] < 0:
        x_comp[9] = 0 # remove: "worsen communication"
      if x_comp[7] < 0:
        x_comp[7] = 0 # remove: "reduce code quality"
      if x_comp[2] < 0:
        x_comp[2] = 0 # remove: "worsen working environment"

      # find 3 suggestions
      x_comp_abs = list(map(abs,x_comp))
      pf_ind = [x_comp_abs.index(x) for x in sorted(x_comp_abs, reverse=True)[:3]]  # find index of the 3 most problematic features
      s = [t[pj_pred[j]], acc_formatted]
      for i in range(3):
        s.append(features[pf_ind[i]][x_comp[pf_ind[i]]<0])
      s.append(p_id[j])
      out.append(tuple(s))
  else:
    #print("accuracy too low: ", clf_accuracy)
    low_acc(predict_data, weights, p_id)
    return 0

  # output to database if out is not empty
  out_to_db(out)
  #print("out length: ", len(out))
  return 0




