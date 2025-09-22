from flask import Flask, request, jsonify
import psycopg2 # Example using a PostgreSQL driver; use your database's driver

# Database Connection Setup (replace with your actual config)
# In a real app, manage this connection carefully (e.g., using Flask-SQLAlchemy)
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="your_db",
        user="your_username",
        password="your_password"
    )
    return conn

# Flask App Initialization 
app = Flask(__name__)

# API Endpoints

@app.route('/api/developers', methods=['POST'])
def create_developer():
    """
    Endpoint to create a new developer.
    This automatically assigns all 'onboarding' documents to them.
    """
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Step 1: Create the new developer and get their new ID
        cur.execute(
            'INSERT INTO developers (name, email) VALUES (%s, %s) RETURNING id',
            (name, email)
        )
        new_developer_id = cur.fetchone()[0]

        # Step 2: Find all standard onboarding documents
        cur.execute('SELECT id FROM documents WHERE is_onboarding_document = TRUE')
        onboarding_docs = cur.fetchall()

        # Step 3: Create an assignment for each onboarding document
        if onboarding_docs:
            # Prepare a list of tuples for efficient insertion
            assignments = [(new_developer_id, doc_id[0]) for doc_id in onboarding_docs]
            # Use execute_values or a loop to insert all assignments
            for assignment in assignments:
                cur.execute(
                    'INSERT INTO developer_documents (developer_id, document_id) VALUES (%s, %s)',
                    assignment
                )
        
        # Commit all changes to the database
        conn.commit()

        return jsonify({
            "message": f"Developer {name} created and assigned {len(onboarding_docs)} onboarding documents."
        }), 201

    except Exception as e:
        conn.rollback() # Roll back changes if any step fails
        print(f"Error: {e}")
        return jsonify({"error": "An internal error occurred"}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/me/documents', methods=['GET'])
def get_my_documents():
    """
    Endpoint for a logged-in developer to fetch their assigned documents.
    """
    # In a real app, you'd get the developer's ID from an authentication token
    # For this example, we'll pretend it's passed as a header
    developer_id = request.headers.get('X-Developer-ID')
    if not developer_id:
        return jsonify({"error": "Authentication required"}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT d.title, d.description, d.url, dd.status
            FROM documents d
            JOIN developer_documents dd ON d.id = dd.document_id
            WHERE dd.developer_id = %s
            """,
            (developer_id,)
        )
        rows = cur.fetchall()
        
        # Format the result as a list of dictionaries
        documents = [
            {"title": row[0], "description": row[1], "url": row[2], "status": row[3]}
            for row in rows
        ]

        return jsonify(documents)

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Could not retrieve documents"}), 500
    finally:
        cur.close()
        conn.close()

# To run this Flask application
if __name__ == '__main__':
    app.run(debug=True)
