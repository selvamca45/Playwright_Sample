"""
W1D4 FastAPI Assignment - Student Grade API

A basic REST API built with FastAPI only. It reuses the Day 2 grading scale
and shows the four main REST methods:

    GET     /                      Welcome message and list of endpoints
    GET     /grade/{mark}          Convert a mark (0-100) to a grade
    POST    /students              Add a student with a mark
    GET     /students              List all students (optional ?grade=A filter)
    GET     /students/{id}         Get one student
    PUT     /students/{id}         Update a student's name or mark
    DELETE  /students/{id}         Remove a student

    
    Method	Endpoint	Purpose
GET	/	Welcome message and a list of endpoints
GET	/grade/85	Converts a mark to a grade (gives B)
POST	/students	Adds a student: {"name": "Selva", "mark": 92}
GET	/students?grade=A	Lists students, with an optional grade filter
GET / PUT / DELETE	/students/{id}	Gets, updates or removes one student

Run:   uvicorn main:app --reload
Docs:  http://127.0.0.1:8000/docs
"""

from typing import Optional

from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title="Student Grade API",
    description="W1D4 FastAPI assignment: a basic REST API that grades student marks.",
    version="1.0.0",
)


# ---------- Grading logic (same scale as Day 2) ----------

def get_grade(mark: float) -> str:
    """Return the letter grade for a mark between 0 and 100 (boundaries inclusive)."""
    if mark >= 90:
        return "A"
    elif mark >= 80:
        return "B"
    elif mark >= 70:
        return "C"
    elif mark >= 60:
        return "D"
    return "E"


# ---------- Data models ----------

class StudentIn(BaseModel):
    """What the client sends when adding a student."""
    name: str = Field(..., min_length=1, max_length=50, examples=["Selva"])
    mark: float = Field(..., ge=0, le=100, examples=[85])


class StudentUpdate(BaseModel):
    """Fields that can be changed. Send only the ones you want to update."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    mark: Optional[float] = Field(None, ge=0, le=100)


class StudentOut(BaseModel):
    """What the API returns for a student."""
    id: int
    name: str
    mark: float
    grade: str


# ---------- In-memory "database" ----------
# Data is kept while the server runs and resets when it restarts.

students: dict[int, dict] = {}
next_id = 1


def to_out(student_id: int) -> StudentOut:
    s = students[student_id]
    return StudentOut(id=student_id, name=s["name"], mark=s["mark"], grade=get_grade(s["mark"]))


def find_or_404(student_id: int) -> None:
    if student_id not in students:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found")


# ---------- Endpoints ----------

@app.get("/", tags=["General"])
def home():
    """Welcome message and a list of available endpoints."""
    return {
        "message": "Welcome to the Student Grade API",
        "docs": "/docs",
        "endpoints": [
            "GET /grade/{mark}",
            "POST /students",
            "GET /students",
            "GET /students/{id}",
            "PUT /students/{id}",
            "DELETE /students/{id}",
        ],
    }


@app.get("/grade/{mark}", tags=["Grades"])
def grade_for_mark(mark: float = Path(..., ge=0, le=100, description="A mark from 0 to 100")):
    """Convert a single mark into its letter grade."""
    return {"mark": mark, "grade": get_grade(mark)}


@app.post("/students", response_model=StudentOut, status_code=201, tags=["Students"])
def add_student(student: StudentIn):
    """Add a new student. The grade is calculated automatically."""
    global next_id
    student_id = next_id
    students[student_id] = {"name": student.name.strip(), "mark": student.mark}
    next_id += 1
    return to_out(student_id)


@app.get("/students", response_model=list[StudentOut], tags=["Students"])
def list_students(grade: Optional[str] = Query(None, pattern="^[A-Ea-e]$",
                                               description="Only show students with this grade")):
    """List all students, optionally filtered by grade (A to E)."""
    result = [to_out(sid) for sid in students]
    if grade:
        result = [s for s in result if s.grade == grade.upper()]
    return result


@app.get("/students/{student_id}", response_model=StudentOut, tags=["Students"])
def get_student(student_id: int):
    """Get one student by id."""
    find_or_404(student_id)
    return to_out(student_id)


@app.put("/students/{student_id}", response_model=StudentOut, tags=["Students"])
def update_student(student_id: int, changes: StudentUpdate):
    """Update a student's name and/or mark. The grade is recalculated."""
    find_or_404(student_id)
    if changes.name is not None:
        students[student_id]["name"] = changes.name.strip()
    if changes.mark is not None:
        students[student_id]["mark"] = changes.mark
    return to_out(student_id)


@app.delete("/students/{student_id}", tags=["Students"])
def delete_student(student_id: int):
    """Remove a student."""
    find_or_404(student_id)
    removed = students.pop(student_id)
    return {"message": f"Student '{removed['name']}' (id {student_id}) deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)