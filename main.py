from typing import Optional, List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import pymongo
from pymongo import MongoClient

from bson.objectid import ObjectId

from pydantic import BaseModel

#connect with server
#client = MongoClient('localhost', 27017) #how to connect to database created via docker??????
client = MongoClient("mongodb+srv://admin:admin@todo-list.he9f8.mongodb.net/test?authSource=admin&replicaSet=atlas-120unt-shard-0&readPreference=primary&appname=MongoDB%20Compass%20Community&ssl=true")
db = client.todolist

#api
app = FastAPI()

#cors
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#data models
class User(BaseModel):
    name: str
    password: str
    email: str    

class Project(BaseModel):
    projectname: str
    user_id: str

class Task(BaseModel):
    taskname: str
    taskfinished: Optional[bool] = False
    project_id: str

#?????
class Login(BaseModel):
    email: str    
    password: str
    


"""
GETS
"""

#returns all users
@app.get("/api/user")
def get_users() -> List[User]:
    users = db.users
    all_users = []
    for user in users.find():
        all_users.append({
            "name": user["name"],
            "email": user["email"],
            "id": str(user["_id"]),
        })
    return all_users


#returns projects per user and optionally tasks per project
@app.get("/api/user/{user_id}")
def get_projects_or_tasks(user_id: str, project_id: Optional[str] = None):
    
    #if no project given, return projects
    if project_id == None:        
        projects = db.projects   
        requested_projects = []

        for project in projects.find({'user_id': user_id}):            
            requested_projects.append({"projectname": project["projectname"],
                                        "project_id": str(project["_id"])})
        return requested_projects

    #if project given, return tasks from project
    if project_id != None:
        tasks = db.tasks
        requested_tasks = []

        for task in tasks.find({'project_id': project_id}):
            requested_tasks.append({"taskname": task["taskname"],
                                    "task_id": str(task["_id"]),
                                    "taskfinished": task["taskfinished"]})
        return requested_tasks


"""
POSTS
"""

#add new user
@app.post("/api/add_user")
async def post_new_user(user: User):
    users = db.users
    users.insert_one(user.dict())
    return user

#log in
@app.post("/api/")
async def user_log_in(login: Login):
    users = db.users
    login_dict = login.dict()
    user_to_login = users.find_one({"email": login_dict["email"]})
    if user_to_login == None:
        return {"msg" : "User not found!", "auth": False}
    if user_to_login["password"] == login_dict["password"]:
        return {"msg" : "Login successful", "auth": True, "user_id": str(user_to_login["_id"]), "user_name": user_to_login["name"]}
    else:
        return {"msg" : "Password invalid!", "auth": False}
    

#add new project to existing user
@app.post("/api/add_project")
async def post_new_project(project: Project):
    projects = db.projects
    users = db.users
    project_dict = project.dict()
    
    #we check if the user exists
    if users.count_documents({'_id': ObjectId(project_dict["user_id"])}) > 0:
        projects.insert_one(project_dict)
        return project
    else:
        return {"msg" : "User not found!"}


#add new task to existing project
@app.post("/api/add_task")
async def post_new_task(task: Task):
    tasks = db.tasks
    projects = db.projects
    task_dict = task.dict()

    #we check if the project exists
    if projects.count_documents({'_id': ObjectId(task_dict["project_id"])}) > 0:
        tasks.insert_one(task_dict)
        return task
    else:
        return {"msg" : "Project not found!"}


"""
PUTS
"""

#update existing project
@app.put("/api/update_project/{project_id}")
async def update_project(project: Project, project_id: str):
    projects = db.projects
    project_dict = project.dict()

    #checks if project exists
    if projects.count_documents({'_id': ObjectId(project_id)}) > 0:
        projects.find_one_and_update({'_id': ObjectId(project_id)}, {"$set" : {"projectname" : project_dict["projectname"]}})
        return project_dict
    else:
        return {"msg" : "Project not found!"}

#update existing task
@app.put("/api/update_task/{task_id}")
async def update_task(task: Task, task_id: str):
    tasks = db.tasks
    task_dict = task.dict()

    #checks if tasks exists
    if tasks.count_documents({'_id': ObjectId(task_id)}) > 0:
        tasks.find_one_and_update({'_id': ObjectId(task_id)}, {"$set" : {"taskname" : task_dict["taskname"], "taskfinished" : task_dict["taskfinished"]}})
        return task_dict
    else:
        return {"msg" : "Task not found!"}


"""
DELETES
"""

#delete project and its tasks
@app.delete("/api/delete_project/{project_id}")
async def delete_project(project_id: str):
    projects = db.projects
    tasks = db.tasks

    #check if id exists:
    if projects.count_documents({'_id': ObjectId(project_id)}) > 0:
        count_tasks = tasks.count_documents({'project_id': project_id})
        project_name = projects.find_one({'_id': ObjectId(project_id)})["projectname"]
        
        #first delete the associated tasks
        tasks.delete_many({'project_id': project_id})

        #then delete the project
        projects.delete_one({'_id': ObjectId(project_id)})
            
        return {"msg" : f"Project '{project_name}' (id: {project_id}) and {count_tasks} tasks deleted"}
    else:
        return {"msg" : "Project not found!"}


#delete tasks
@app.delete("/api/delete_task/{task_id}")
async def delete_task(task_id: str):
    tasks = db.tasks

    #check if id exists and delete:
    if tasks.count_documents({'_id': ObjectId(task_id)}) > 0:
        tasks.delete_one({'_id': ObjectId(task_id)})
        return {"msg" : "Task deleted"}
    else:
        return {"msg" : "Task not found!"}

    




