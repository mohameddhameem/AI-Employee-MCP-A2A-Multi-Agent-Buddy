"""
Phase 2: Database Setup Script
Creates SQLite database with employee sample data
"""

import sqlite3
import os
from pathlib import Path

def create_database():
    """Create the SQLite database and tables"""
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Database path
    db_path = data_dir / "employees.db"
    
    # Remove existing database for fresh start
    if db_path.exists():
        os.remove(db_path)
        print(f"🗑️ Removed existing database: {db_path}")
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create employees table
    cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            salary INTEGER NOT NULL,
            email TEXT,
            hire_date TEXT,
            manager_id INTEGER,
            location TEXT,
            FOREIGN KEY (manager_id) REFERENCES employees (id)
        )
    """)
    
    # Create departments table
    cursor.execute("""
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            budget INTEGER,
            head_id INTEGER,
            location TEXT,
            FOREIGN KEY (head_id) REFERENCES employees (id)
        )
    """)
    
    # Create projects table
    cursor.execute("""
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT CHECK(status IN ('Active', 'Completed', 'On Hold')),
            start_date TEXT,
            end_date TEXT,
            budget INTEGER,
            department_id INTEGER,
            FOREIGN KEY (department_id) REFERENCES departments (id)
        )
    """)
    
    conn.commit()
    print(f"✅ Created database with tables: {db_path}")
    return conn

def insert_sample_data(conn):
    """Insert comprehensive sample data"""
    cursor = conn.cursor()
    
    # Sample departments
    departments = [
        (1, "Engineering", 2000000, None, "San Francisco"),
        (2, "Marketing", 800000, None, "New York"), 
        (3, "Sales", 1200000, None, "Chicago"),
        (4, "HR", 500000, None, "Austin"),
        (5, "Finance", 600000, None, "Boston"),
        (6, "Data Science", 1500000, None, "Seattle")
    ]
    
    cursor.executemany("""
        INSERT INTO departments (id, name, budget, head_id, location) 
        VALUES (?, ?, ?, ?, ?)
    """, departments)
    
    # Sample employees
    employees = [
        # Engineering Team
        (1, "Alice Johnson", "Engineering", 120000, "alice.johnson@company.com", "2023-01-15", None, "San Francisco"),
        (2, "Bob Smith", "Engineering", 110000, "bob.smith@company.com", "2023-02-01", 1, "San Francisco"),
        (3, "Carol Davis", "Engineering", 115000, "carol.davis@company.com", "2023-01-20", 1, "San Francisco"),
        (4, "David Wilson", "Engineering", 105000, "david.wilson@company.com", "2023-03-10", 1, "San Francisco"),
        (5, "Eva Brown", "Engineering", 125000, "eva.brown@company.com", "2022-11-01", 1, "San Francisco"),
        
        # Marketing Team
        (6, "Frank Miller", "Marketing", 85000, "frank.miller@company.com", "2023-01-05", None, "New York"),
        (7, "Grace Lee", "Marketing", 75000, "grace.lee@company.com", "2023-02-15", 6, "New York"),
        (8, "Henry Clark", "Marketing", 80000, "henry.clark@company.com", "2023-01-25", 6, "New York"),
        
        # Sales Team  
        (9, "Ivy Taylor", "Sales", 95000, "ivy.taylor@company.com", "2022-12-01", None, "Chicago"),
        (10, "Jack Anderson", "Sales", 88000, "jack.anderson@company.com", "2023-01-30", 9, "Chicago"),
        (11, "Kate Thomas", "Sales", 92000, "kate.thomas@company.com", "2023-02-10", 9, "Chicago"),
        (12, "Liam Garcia", "Sales", 87000, "liam.garcia@company.com", "2023-03-01", 9, "Chicago"),
        
        # HR Team
        (13, "Maya Rodriguez", "HR", 78000, "maya.rodriguez@company.com", "2022-10-15", None, "Austin"),
        (14, "Noah Martinez", "HR", 72000, "noah.martinez@company.com", "2023-01-12", 13, "Austin"),
        
        # Finance Team
        (15, "Olivia White", "Finance", 95000, "olivia.white@company.com", "2022-09-01", None, "Boston"),
        (16, "Paul Harris", "Finance", 85000, "paul.harris@company.com", "2023-01-08", 15, "Boston"),
        
        # Data Science Team
        (17, "Quinn Lewis", "Data Science", 130000, "quinn.lewis@company.com", "2022-08-15", None, "Seattle"),
        (18, "Rachel Walker", "Data Science", 125000, "rachel.walker@company.com", "2023-01-20", 17, "Seattle"),
        (19, "Sam Hall", "Data Science", 120000, "sam.hall@company.com", "2023-02-05", 17, "Seattle"),
        (20, "Tina Young", "Data Science", 118000, "tina.young@company.com", "2023-02-20", 17, "Seattle")
    ]
    
    cursor.executemany("""
        INSERT INTO employees (id, name, department, salary, email, hire_date, manager_id, location) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, employees)
    
    # Update department heads
    dept_heads = [
        (1, 1),  # Alice heads Engineering
        (6, 2),  # Frank heads Marketing  
        (9, 3),  # Ivy heads Sales
        (13, 4), # Maya heads HR
        (15, 5), # Olivia heads Finance
        (17, 6)  # Quinn heads Data Science
    ]
    
    cursor.executemany("""
        UPDATE departments SET head_id = ? WHERE id = ?
    """, dept_heads)
    
    # Sample projects
    projects = [
        (1, "AI Chat Platform", "Build customer service chatbot", "Active", "2023-01-01", "2023-06-30", 500000, 1),
        (2, "Mobile App Redesign", "Redesign mobile application UI/UX", "Active", "2023-02-01", "2023-08-31", 300000, 1),
        (3, "Data Pipeline Optimization", "Improve data processing efficiency", "Completed", "2022-10-01", "2023-01-31", 200000, 6),
        (4, "Brand Campaign Q1", "Marketing campaign for Q1 launch", "Completed", "2023-01-01", "2023-03-31", 150000, 2),
        (5, "Sales Analytics Dashboard", "Real-time sales performance tracking", "Active", "2023-01-15", "2023-07-15", 250000, 6),
        (6, "HR Management System", "Employee onboarding automation", "On Hold", "2023-02-01", "2023-09-30", 180000, 4)
    ]
    
    cursor.executemany("""
        INSERT INTO projects (id, name, description, status, start_date, end_date, budget, department_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, projects)
    
    conn.commit()
    print("✅ Inserted sample data:")
    print(f"   - {len(departments)} departments")
    print(f"   - {len(employees)} employees") 
    print(f"   - {len(projects)} projects")

def verify_data(conn):
    """Verify the data was inserted correctly"""
    cursor = conn.cursor()
    
    print("\n📊 Database Verification:")
    print("=" * 40)
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM employees")
    emp_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM departments")  
    dept_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM projects")
    proj_count = cursor.fetchone()[0]
    
    print(f"📋 Total employees: {emp_count}")
    print(f"🏢 Total departments: {dept_count}")
    print(f"🚀 Total projects: {proj_count}")
    
    # Sample queries
    print("\n🔍 Sample Queries:")
    print("-" * 20)
    
    # Average salary by department
    cursor.execute("""
        SELECT department, AVG(salary) as avg_salary, COUNT(*) as count
        FROM employees 
        GROUP BY department 
        ORDER BY avg_salary DESC
    """)
    
    print("💰 Average Salary by Department:")
    for row in cursor.fetchall():
        dept, avg_sal, count = row
        print(f"   {dept}: ${avg_sal:,.0f} ({count} employees)")
    
    # Active projects
    cursor.execute("""
        SELECT p.name, d.name as department, p.budget 
        FROM projects p 
        JOIN departments d ON p.department_id = d.id 
        WHERE p.status = 'Active'
        ORDER BY p.budget DESC
    """)
    
    print("\n🚀 Active Projects:")
    for row in cursor.fetchall():
        proj_name, dept, budget = row
        print(f"   {proj_name} ({dept}): ${budget:,}")

if __name__ == "__main__":
    print("🗄️ Phase 2: Creating Employee Database")
    print("=" * 50)
    
    # Create database and tables
    conn = create_database()
    
    # Insert sample data
    insert_sample_data(conn)
    
    # Verify everything works
    verify_data(conn)
    
    # Close connection
    conn.close()
    
    print("\n✅ Phase 2 Complete!")
    print("📁 Database created at: ./data/employees.db")
    print("🎯 Ready for Phase 3: Build MCP Server")
