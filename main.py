from flask import Flask, request, jsonify
from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# MongoDB setup from .env
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "mockDB")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mockCollection")

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
except errors.ConnectionFailure as e:
    print(f"MongoDB connection failed: {e}")
    collection = None

def build_response(status_code, message, body=None):
    return jsonify({
        "status_code": status_code,
        "message": message,
        "body": body
    }), status_code

# Insert data
@app.route("/push", methods=["POST"])
def push_data():
    try:
        data = request.json
        if not data:
            return build_response(400, "No data provided", None)

        result = collection.insert_one(data)
        return build_response(201, "Data inserted", {"id": str(result.inserted_id)})

    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})

# Get data
@app.route("/get", methods=["GET"])
def get_data():
    try:
        docs = list(collection.find({}, {"_id": 0}))
        if not docs:
            return build_response(200, "No data found", [])

        return build_response(200, "Data fetched successfully", docs)

    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) 
    app.run(host="0.0.0.0", port=port, debug=True)
