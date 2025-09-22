from flask import Flask, request, jsonify

# FAKE IN-MEMORY DATABASE (for simple testing) 
# This dictionary will act as our database.
db = {
    "developers": [],
    "documents": [
        # Pre-load one onboarding document for the test
        {
            "id": 101,
            "title": "Onboarding Guide",
            "description": "Your first steps in our team.",
            "url": "http://example.com/guide",
            "is_onboarding_document": True
        },
        {
            "id": 102,
            "title": "Advanced Project X Docs",
            "description": "Internal docs for Project X.",
            "url": "http://example.com/project-x",
            "is_onboarding_document": False
        }
    ],
    "developer_documents": []
}
# These will act as our auto-incrementing IDs
next_developer_id = 1
# END OF FAKE DATABASE SETUP 


app = Flask(__name__)


@app.route('/api/developers', methods=['POST'])
def create_developer():
    """Creates a developer and assigns docs using the FAKE database."""
    global next_developer_id
    data = request.get_json()

    # Create the new developer object
    new_developer = {
        "id": next_developer_id,
        "name": data.get('name'),
        "email": data.get('email')
    }
    db["developers"].append(new_developer)

    # Find onboarding docs and assign them
    docs_assigned_count = 0
    for doc in db["documents"]:
        if doc["is_onboarding_document"]:
            assignment = {
                "developer_id": new_developer["id"],
                "document_id": doc["id"],
                "status": "assigned"
            }
            db["developer_documents"].append(assignment)
            docs_assigned_count += 1
    
    # Increment the ID for the next user
    next_developer_id += 1

    return jsonify({
        "message": f"Developer {data.get('name')} created and assigned {docs_assigned_count} onboarding documents."
    }), 201


@app.route('/api/me/documents', methods=['GET'])
def get_my_documents():
    """Gets assigned documents for a developer from the FAKE database."""
    developer_id_str = request.headers.get('X-Developer-ID')
    
    if not developer_id_str:
        return jsonify({"error": "X-Developer-ID header is required"}), 401

    developer_id = int(developer_id_str)
    
    # Find the assignments for this developer
    my_assignments = [
        assign for assign in db["developer_documents"] if assign["developer_id"] == developer_id
    ]
    
    # Find the full details for each assigned document
    my_docs = []
    for assignment in my_assignments:
        for doc in db["documents"]:
            if doc["id"] == assignment["document_id"]:
                my_docs.append({
                    "title": doc["title"],
                    "description": doc["description"],
                    "url": doc["url"],
                    "status": assignment["status"]
                })
                break # Move to the next assignment

    return jsonify(my_docs)


# To run this Flask application
if __name__ == '__main__':
    app.run(debug=True, port=5000)
