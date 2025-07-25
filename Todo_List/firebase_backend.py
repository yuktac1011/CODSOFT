# firebase_backend.py

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# --- SETUP ---
# Make sure your serviceAccountKey.json is in the same directory
try:
    cred = credentials.Certificate('serviceAccountKey.json')
    # Prevent re-initializing the app which causes an error
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"🔴 Could not initialize Firebase. Make sure 'serviceAccountKey.json' is correct. Error: {e}")

db = firestore.client()
# Make sure this collection name matches what you have in your Firestore database.
tasks_ref = db.collection('todos') 


# --- CORRECTED FUNCTION ---
# We add `due_date=None` to the function signature.
# This means it's an optional argument.
def add_task(text: str, due_date=None):
    """
    Adds a new task to the 'todos' collection.
    Now correctly accepts an optional due_date.
    """
    if text.strip():
        tasks_ref.add({
            'text': text,
            'completed': False,
            'created_at': firestore.SERVER_TIMESTAMP, # This is a great way to set the time!
            'due_date': due_date, # This now works because due_date is a parameter
            'notified': False # Added for the external notifier concept
        })


def update_task(task_id: str, data: dict):
    """Updates an existing task document."""
    tasks_ref.document(task_id).update(data)


def delete_task(task_id: str):
    """Deletes a task document by its ID."""
    tasks_ref.document(task_id).delete()


def get_tasks():
    """Retrieves all tasks, ordered by creation date."""
    # This correctly returns a list of DocumentSnapshot objects that main.py can use.
    return list(tasks_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream())