from flask import Flask, request, jsonify
from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
import cloudinary
import cloudinary.uploader
from datetime import datetime
from bson import ObjectId
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)

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

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        if not data or "user_id" not in data or "password" not in data:
            return build_response(400, "user_id and password are required", None)

        user_id = data["user_id"]
        password = data["password"]

        existing_user = collection.find_one({"user_id": user_id})
        if existing_user:
            return build_response(409, "User ID already exists", None)

        # Insert new user
        result = collection.insert_one({
            "user_id": user_id,
            "password": password  
        })

        return build_response(
            201,
            "User registered successfully",
            {"id": str(result.inserted_id), "user_id": user_id}
        )

    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})


@app.route("/push-cattle", methods=["POST"])
def push_cattle():
    try:
        data = request.json
        if not data:
            return build_response(400, "No data provided", None)

        required_fields = ["user_id", "tag_number", "species", "breed"]
        for field in required_fields:
            if field not in data:
                return build_response(400, f"Missing required field: {field}", None)

        user_id = data["user_id"]
        breed_name = data["breed"]   # 👈 breed name from request (e.g. "Gir")

        # ✅ Check if user exists
        user = collection.find_one({"user_id": user_id})
        if not user:
            return build_response(404, "User not found", None)

        # ✅ Search breed in Breed collection by BreedName
        breed_collection = db["Breed"]
        breed = breed_collection.find_one({"BreedName": breed_name})
        if not breed:
            return build_response(404, f"Breed '{breed_name}' not found", None)

        cattle_doc = {
            "name": data.get("name"),
            "tag_number": data["tag_number"],
            "data_entry_date": data.get("data_entry_date", datetime.utcnow().strftime("%Y-%m-%d")),
            "tagging_date": data.get("tagging_date"),
            "species": data["species"],
            "sex": data.get("sex"),
            "dob": data.get("dob"),
            "breed_id": str(breed["_id"]),     # store Mongo ObjectId
            "breed_name": breed["BreedName"]   # take from Breed collection
        }

        collection.update_one(
            {"user_id": user_id},
            {"$push": {"cattles": cattle_doc}}
        )

        return build_response(
            201,
            "Cattle added successfully to user",
            {
                "user_id": user_id,
                "tag_number": data["tag_number"],
                "breed_id": str(breed["_id"]),
                "breed_name": breed["BreedName"]
            }
        )

    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})



@app.route("/get-cattle", methods=["GET"])
def get_cattle():
    try:
        user_id = request.args.get("userId")
        if not user_id:
            return build_response(400, "userId is required as query parameter", None)

        user = collection.find_one({"user_id": user_id}, {"_id": 0, "cattles": 1})
        if not user:
            return build_response(404, "User not found", None)

        cattles = user.get("cattles", [])
        return build_response(200, "Cattle data fetched successfully", cattles)

    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})
    

@app.route("/get-breed/<breed_id>", methods=["GET"])
def get_breed_by_id(breed_id):
    try:
        breed_collection = db["Breed"]
        # Route to fetch breed details by breed_id
        if not ObjectId.is_valid(breed_id):
            return build_response(400, "Invalid breed_id format", None)

        # 🔍 Find by MongoDB ObjectId
        breed = breed_collection.find_one({"_id": ObjectId(breed_id)}, {"_id": 0})
        if not breed:
            return build_response(404, f"Breed with id {breed_id} not found", None)

        return build_response(200, "Breed fetched successfully", breed)

    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})
    
    
@app.route("/upload-image", methods=["POST"])
def upload_image():
    try:
        if 'image' not in request.files:
            return build_response(400, "No image file provided", None)

        image_file = request.files['image']

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
