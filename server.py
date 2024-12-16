from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Models
class TaskBase(BaseModel):
    name: str
    completed: bool = False
    weight: int = 1  # Task weight for scoring

class Task(TaskBase):
    id: str

class ProjectBase(BaseModel):
    name: str
    description: str
    assigned_to: Optional[str] = None 
    tasks: List[Task] = [] 
    score: int = 0  

class Project(ProjectBase):
    id: str
    progress: int = 0  
    completed: bool = False

class TaskUpdate(BaseModel):
    completed: bool

projects_db: List[Project] = []

# Utility function to calculate progress and score
def calculate_progress_and_score(project: Project) -> tuple[int, int]:
    total_tasks = len(project.tasks)
    if total_tasks == 0:
        return 0, 0
    completed_tasks = [task for task in project.tasks if task.completed]
    progress = int((len(completed_tasks) / total_tasks) * 100)
    score = sum(task.weight for task in completed_tasks)
    return progress, score


# Get all projects
@app.get("/projects", response_model=List[Project])
def get_projects():
    return projects_db

# Create a new project
@app.post("/projects", response_model=Project)
def create_project(project: ProjectBase):
    if not project.assigned_to:
        raise HTTPException(status_code=400, detail="Project must be assigned to a user.")
    new_project = Project(id=str(uuid4()), **project.dict())
    projects_db.append(new_project)
    return new_project

# Add a task to a project
@app.post("/projects/{project_id}/tasks", response_model=Task)
def add_task(project_id: str, task: TaskBase):
    for project in projects_db:
        if project.id == project_id:
            new_task = Task(id=str(uuid4()), **task.dict())
            project.tasks.append(new_task)
            project.progress, project.score = calculate_progress_and_score(project)
            return new_task
    raise HTTPException(status_code=404, detail="Project not found")

# Mark a task as completed
@app.put("/projects/{project_id}/tasks/{task_id}/complete", response_model=Project)
def complete_task(project_id: str, task_id: str):
    for project in projects_db:
        if project.id == project_id:
            for task in project.tasks:
                if task.id == task_id:
                    task.completed = True
                    project.progress, project.score = calculate_progress_and_score(project)
                    project.completed = project.progress == 100
                    return project
    raise HTTPException(status_code=404, detail="Task or Project not found")

# Delete a project
@app.delete("/projects/{project_id}")
def delete_project(project_id: str):
    global projects_db
    projects_db = [project for project in projects_db if project.id != project_id]
    return {"message": "Project deleted successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
