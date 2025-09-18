from flask import Flask, request, jsonify
from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
import cloudinary
import cloudinary.uploader

load_dotenv()

app = Flask(__name__)

# MongoDB setup
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

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

def build_response(status_code, message, body=None):
    return jsonify({
        "status_code": status_code,
        "message": message,
        "body": body
    }), status_code

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

@app.route("/get", methods=["GET"])
def get_data():
    try:
        docs = list(collection.find({}, {"_id": 0}))
        if not docs:
            return build_response(200, "No data found", [])

        return build_response(200, "Data fetched successfully", docs)

    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})

@app.route("/upload-image", methods=["POST"])
def upload_image():
    try:
        if 'image' not in request.files:
            return build_response(400, "No image file provided", None)

        image_file = request.files['image']

        # Optional metadata
        metadata = {
            "name": request.form.get("name"),
            "description": request.form.get("description")
        }

        upload_result = cloudinary.uploader.upload(
            image_file,
            folder="Model" 
        )

        doc = {
            "url": upload_result.get("secure_url"),
            **metadata
        }
        result = collection.insert_one(doc)

        return build_response(
            201,
            "Image uploaded successfully",
            {"id": str(result.inserted_id), "url": upload_result.get("secure_url")}
        )

    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
