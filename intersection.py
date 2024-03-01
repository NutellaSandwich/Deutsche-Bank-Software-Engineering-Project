import sqlite3


def intersection(proj_id):
    # Computes the jaccard coefficient of a given project with the technology skills of the team members.
    # Parameter: proj_id (int) - project id to calculate for.
    # Returns: jaccard_coefficient - jaccard coefficient for the given project
    
    conn = sqlite3.connect('database.sqlite')
    c = conn.cursor()

    ptech = c.execute("SELECT technology_id FROM project_technology WHERE project_id = ?", (proj_id,)).fetchall()
    # ptech = db.session.query(ProjectTechnology.technology_id).filter(ProjectTechnology.project_id==proj_id).all()

    utech = c.execute("SELECT technology_id FROM user_technology, user_project_relation WHERE user_technology.user_id == user_project_relation.user_id AND user_project_relation.project_id=? AND user_technology.yearsExperience > 0", (proj_id,)).fetchall()

    # utech = db.session.query(UserTechnology.technology_id).join(UserProjectRelation, UserTechnology.user_id==UserProjectRelation.user_id).filter(UserProjectRelation.project_id==proj_id, UserTechnology.yearsExperience>0).all()

    project_technology_ids = set(tech_id for (tech_id,) in ptech) # set of technology ids used in project
    team_technology_ids = set(tech_id for (tech_id,) in utech)# set of technology ids team has
    missing_technologies = set(project_technology_ids.difference(team_technology_ids))
    if (len(project_technology_ids) == 0): return 1
    jaccard_coefficient = 1 - (len(missing_technologies) / len(project_technology_ids))

    c.close()
    conn.close()

    return jaccard_coefficient
