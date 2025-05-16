# HIGH SEVERITY: SQL Injection vulnerability
# File: src/database/user_repository.py

import sqlite3
import mysql.connector

class UserRepository:
    def __init__(self, db_connection):
        self.connection = db_connection
    
    # HIGH SEVERITY: SQL Injection vulnerability
    def find_user_by_username(self, username):
        """
        Find a user by their username.
        WARNING: This function is vulnerable to SQL injection attacks!
        """
        cursor = self.connection.cursor()
        
        # Vulnerable code: Direct string interpolation in SQL query
        query = f"SELECT * FROM users WHERE username = '{username}'"
        cursor.execute(query)
        
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2]
            }
        return None
    
    # Safe version that uses parameterized queries
    def find_user_safely(self, username):
        """Find a user by their username safely using parameterized queries."""
        cursor = self.connection.cursor()
        
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return {
                'id': result[0],
                'username': result[1],
                'email': result[2]
            }
        return None


# Usage example
if __name__ == "__main__":
    # This is just for demonstration
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",  # Another issue: hardcoded credentials
        database="userdb"
    )
    
    repo = UserRepository(conn)
    
    # Vulnerable to SQL injection
    user = repo.find_user_by_username("admin' OR '1'='1")
    print(user)