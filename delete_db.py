import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'db.sqlite3')

# Try to delete the database file
try:
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Database file deleted successfully!")
    else:
        print("Database file does not exist.")
except Exception as e:
    print(f"Error deleting database file: {str(e)}") 