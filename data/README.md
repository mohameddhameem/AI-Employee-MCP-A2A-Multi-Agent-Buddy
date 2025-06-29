# Data Folder

This folder contains the SQLite database and database utilities for the RAG agent project.

## Files

- **`employees.db`** - SQLite database with sample employee, department, and project data
- **`database_utils.py`** - Python utility class for querying the database

## Database Schema

### Employees Table
- `id` - Primary key
- `name` - Employee full name  
- `department` - Department name
- `salary` - Annual salary
- `email` - Work email address
- `hire_date` - Date hired (YYYY-MM-DD)
- `manager_id` - Foreign key to manager's employee ID
- `location` - Office location

### Departments Table  
- `id` - Primary key
- `name` - Department name
- `budget` - Annual budget
- `head_id` - Foreign key to department head's employee ID
- `location` - Primary office location

### Projects Table
- `id` - Primary key
- `name` - Project name
- `description` - Project description
- `status` - Active, Completed, or On Hold
- `start_date` - Project start date
- `end_date` - Planned/actual end date
- `budget` - Project budget
- `department_id` - Foreign key to owning department

## Sample Data

- **20 employees** across 6 departments
- **6 departments**: Engineering, Data Science, Sales, Marketing, HR, Finance
- **6 projects** with various statuses
- Realistic salary ranges and organizational structure

## Usage

```python
from data.database_utils import EmployeeDB

db = EmployeeDB()
employees = db.get_all_employees()
engineering_team = db.get_employees_by_department("Engineering")
summary = db.get_employee_summary()
```
