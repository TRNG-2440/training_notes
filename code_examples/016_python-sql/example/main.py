from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
from dao import EmployeeDAO, EmployeeRecord

app = FastAPI()
dao = EmployeeDAO()


# =============================================================================
# PYDANTIC MODELS — API Layer
# Responsibility: validate and sanitize data coming in from external clients.
# These models are entirely separate from the database layer dataclasses.
# =============================================================================
class CreateEmployeeRequest(BaseModel):
    emp_name: str
    emp_title: str
    emp_salary: float

    @field_validator("emp_salary")
    def salary_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError("Salary must be a positive value")
        return value


class UpdateEmployeeRequest(BaseModel):
    # Used for PUT — all fields are required for a full replacement
    emp_name: str
    emp_title: str
    emp_salary: float

    @field_validator("emp_salary")
    def salary_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError("Salary must be a positive value")
        return value


class PatchEmployeeRequest(BaseModel):
    # Used for PATCH — all fields are Optional so only provided fields are updated
    emp_name: Optional[str] = None
    emp_title: Optional[str] = None
    emp_salary: Optional[float] = None

    @field_validator("emp_salary")
    def salary_must_be_positive(cls, value):
        if value is not None and value <= 0:
            raise ValueError("Salary must be a positive value")
        return value


class EmployeeResponse(BaseModel):
    # Defines the shape of every API response containing an employee record
    emp_id: int
    emp_name: str
    emp_title: str
    emp_salary: float


# =============================================================================
# HELPER — converts an EmployeeRecord dataclass to an EmployeeResponse model.
# Used in every endpoint to produce the API response from a DAO return value.
# Note: this function does not do much besides converting to the correct type.
# However, this utility function can have more complex functionality.
#
# For instance, if EmployeeResponse did not contain the 'id' because it is
# sensitive data, this helper function would ignore that field of the
# EmployeeRecord dataclass
# =============================================================================
def to_response(record: EmployeeRecord) -> EmployeeResponse:
    return EmployeeResponse(
        emp_id=record.emp_id,
        emp_name=record.emp_name,
        emp_title=record.emp_title,
        emp_salary=record.emp_salary
    )


# =============================================================================
# ENDPOINTS
# Each endpoint follows the same pattern:
#   1. Validate input via Pydantic (automatic for request body, manual for path params)
#   2. Convert to EmployeeRecord and call the appropriate DAO method
#   3. Handle the case where a record is not found (404)
#   4. Convert the returned EmployeeRecord to an EmployeeResponse and return it
# =============================================================================
@app.get("/employees", response_model=list[EmployeeResponse])
def get_all_employees():
    records = dao.get_all()
    return [to_response(record) for record in records]

@app.get("/employees/{emp_id}", response_model=EmployeeResponse)
def get_employee(emp_id: int):
    record = dao.get_by_id(emp_id)
    if not record:
        raise HTTPException(status_code=404, detail="Employee not found")
    return to_response(record)

@app.post("/employees", response_model=EmployeeResponse, status_code=201)
def create_employee(request: CreateEmployeeRequest):
    # Convert the validated Pydantic request model to a database layer dataclass.
    # emp_id is None — the database generates this on INSERT.
    record = EmployeeRecord(
        emp_id=None,
        emp_name=request.emp_name,
        emp_title=request.emp_title,
        emp_salary=request.emp_salary
    )
    saved = dao.create(record)
    return to_response(saved)


@app.put("/employees/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: int, request: UpdateEmployeeRequest):
    # PUT is a full replacement — all fields are provided and the record
    # is overwritten entirely. We construct the EmployeeRecord with the
    # incoming values and pass it directly to the DAO.
    record = EmployeeRecord(
        emp_id=emp_id,
        emp_name=request.emp_name,
        emp_title=request.emp_title,
        emp_salary=request.emp_salary
    )
    updated = dao.update(record)
    if not updated:
        raise HTTPException(status_code=404, detail="Employee not found")
    return to_response(updated)


@app.patch("/employees/{emp_id}", response_model=EmployeeResponse)
def patch_employee(emp_id: int, request: PatchEmployeeRequest):
    # PATCH is a partial update — only the fields provided in the request
    # body should change. We first fetch the existing record, then apply
    # only the non-None values from the request before passing to the DAO.
    existing = dao.get_by_id(emp_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Apply only the fields that were included in the PATCH request
    updated_record = EmployeeRecord(
        emp_id=emp_id,
        emp_name=request.emp_name if request.emp_name is not None else existing.emp_name,
        emp_title=request.emp_title if request.emp_title is not None else existing.emp_title,
        emp_salary=request.emp_salary if request.emp_salary is not None else existing.emp_salary
    )
    updated = dao.update(updated_record)
    return to_response(updated)


@app.delete("/employees/{emp_id}", status_code=204)
def delete_employee(emp_id: int):
    # dao.delete() returns True if a record was deleted, False if not found
    deleted = dao.delete(emp_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Employee not found")
    # 204 No Content — successful deletion returns no response body