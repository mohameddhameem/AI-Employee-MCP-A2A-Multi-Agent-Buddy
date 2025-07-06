"""
Database Query Utility
Provides functions to query the employee database for the MCP server
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

class EmployeeDB:
    """Employee database query utility"""
    
    def __init__(self, db_path: str = "./data/employees.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_employees(self) -> List[Dict[str, Any]]:
        """Get all employees"""
        query = """
            SELECT id, name, department, salary, email, hire_date, manager_id, location
            FROM employees
            ORDER BY department, name
        """
        return self._execute_query(query)
    
    def get_employees_by_department(self, department: str) -> List[Dict[str, Any]]:
        """Get employees by department"""
        query = """
            SELECT id, name, department, salary, email, hire_date, manager_id, location
            FROM employees 
            WHERE department = ?
            ORDER BY name
        """
        return self._execute_query(query, (department,))
    
    def get_employee_by_id(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Get employee by ID"""
        query = """
            SELECT id, name, department, salary, email, hire_date, manager_id, location
            FROM employees 
            WHERE id = ?
        """
        results = self._execute_query(query, (employee_id,))
        return results[0] if results else None
    
    def get_department_summary(self) -> List[Dict[str, Any]]:
        """Get department summary with employee count and average salary"""
        query = """
            SELECT 
                department,
                COUNT(*) as employee_count,
                AVG(salary) as avg_salary,
                MIN(salary) as min_salary,
                MAX(salary) as max_salary
            FROM employees 
            GROUP BY department
            ORDER BY avg_salary DESC
        """
        return self._execute_query(query)
    
    def get_employees_by_salary_range(self, min_salary: int, max_salary: int) -> List[Dict[str, Any]]:
        """Get employees within salary range"""
        query = """
            SELECT id, name, department, salary, email, hire_date, location
            FROM employees 
            WHERE salary BETWEEN ? AND ?
            ORDER BY salary DESC
        """
        return self._execute_query(query, (min_salary, max_salary))
    
    def get_managers_and_reports(self) -> List[Dict[str, Any]]:
        """Get managers with their direct reports"""
        query = """
            SELECT 
                m.id as manager_id,
                m.name as manager_name,
                m.department as manager_department,
                e.id as employee_id,
                e.name as employee_name,
                e.salary as employee_salary
            FROM employees m
            JOIN employees e ON m.id = e.manager_id
            ORDER BY m.name, e.name
        """
        return self._execute_query(query)
    
    def get_departments(self) -> List[Dict[str, Any]]:
        """Get all departments with details"""
        query = """
            SELECT 
                d.id, d.name, d.budget, d.location,
                e.name as head_name
            FROM departments d
            LEFT JOIN employees e ON d.head_id = e.id
            ORDER BY d.name
        """
        return self._execute_query(query)
    
    def get_active_projects(self) -> List[Dict[str, Any]]:
        """Get active projects"""
        query = """
            SELECT 
                p.id, p.name, p.description, p.status, p.budget,
                p.start_date, p.end_date,
                d.name as department_name
            FROM projects p
            JOIN departments d ON p.department_id = d.id
            WHERE p.status = 'Active'
            ORDER BY p.budget DESC
        """
        return self._execute_query(query)
    
    def search_employees(self, search_term: str) -> List[Dict[str, Any]]:
        """Search employees by name or email"""
        query = """
            SELECT id, name, department, salary, email, hire_date, location
            FROM employees 
            WHERE name LIKE ? OR email LIKE ?
            ORDER BY name
        """
        pattern = f"%{search_term}%"
        return self._execute_query(query, (pattern, pattern))
    
    def get_employee_summary(self) -> Dict[str, Any]:
        """Get overall employee statistics"""
        queries = {
            "total_employees": "SELECT COUNT(*) as count FROM employees",
            "total_departments": "SELECT COUNT(DISTINCT department) as count FROM employees", 
            "avg_salary": "SELECT AVG(salary) as avg FROM employees",
            "total_budget": "SELECT SUM(salary) as total FROM employees"
        }
        
        summary = {}
        for key, query in queries.items():
            result = self._execute_query(query)
            if key in ["avg_salary", "total_budget"]:
                summary[key] = round(result[0][list(result[0].keys())[0]], 2)
            else:
                summary[key] = result[0][list(result[0].keys())[0]]
        
        return summary

# Test the database functions
if __name__ == "__main__":
    print("Testing Database Query Utility")
    print("=" * 40)
    
    try:
        db = EmployeeDB()
        
        # Test basic queries
        print("All Employees:")
        employees = db.get_all_employees()
        for emp in employees[:3]:  # Show first 3
            print(f"   {emp['name']} - {emp['department']} - ${emp['salary']:,}")
        print(f"   ... and {len(employees)-3} more")
        
        print(f"\nEngineering Department:")
        eng_employees = db.get_employees_by_department("Engineering")
        for emp in eng_employees:
            print(f"   {emp['name']} - ${emp['salary']:,}")
        
        print(f"\nDepartment Summary:")
        summary = db.get_department_summary()
        for dept in summary:
            print(f"   {dept['department']}: {dept['employee_count']} employees, avg ${dept['avg_salary']:,.0f}")
        
        print(f"\nOverall Statistics:")
        stats = db.get_employee_summary()
        print(f"   Total Employees: {stats['total_employees']}")
        print(f"   Total Departments: {stats['total_departments']}")
        print(f"   Average Salary: ${stats['avg_salary']:,.0f}")
        print(f"   Total Payroll: ${stats['total_budget']:,.0f}")
        
        print("\nSUCCESS: Database Query Utility working correctly!")
        
    except Exception as e:
        print(f"ERROR: {e}")
