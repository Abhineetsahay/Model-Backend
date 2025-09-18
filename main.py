from flask import Flask, request, jsonify
from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
import cloudinary
import cloudinary.uploader
from datetime import datetime
from bson.objectid import ObjectId
from PIL import Image
import torch
import io
from torchvision import transforms
from PIL import Image
import torch
import io
from torchvision import transforms
import torch.nn.functional as F

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
        breed_name = data["breed"]

        user = collection.find_one({"user_id": user_id})
        if not user:
            return build_response(404, "User not found", None)

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
            "breed_id": str(breed["_id"]),
            "breed_name": breed["BreedName"]
        }

        collection.update_one(
            {"user_id": user_id},
            {"$push": {"cattles": cattle_doc}}
        )

        return build_response(
            201,
            "Cattle added successfully",
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

        return build_response(200, "Cattle data fetched successfully", user.get("cattles", []))

    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})


@app.route("/upload-and-predict", methods=["POST"])
def upload_and_predict():
    try:
        if 'image' not in request.files:
            return build_response(400, "No image file provided", None)

        image_file = request.files['image']

        metadata = {
            "name": request.form.get("name"),
            "description": request.form.get("description")
        }

        model = torch.load("breed_classifier_production.pt", map_location=torch.device("cpu"), weights_only=False)
        model.eval()

        img_bytes = image_file.read()
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        preprocess = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ])
        input_tensor = preprocess(image).unsqueeze(0)

        with torch.no_grad():
            output = model(input_tensor)
            probabilities = F.softmax(output, dim=1) 
            top_probs, top_idxs = torch.topk(probabilities, 3)  

        class_labels = ['Alambadi', 'Amritmahal', 'Ayrshire', 'Banni', 'Bargur', 'Bhadawari', 'Brown Swiss', 'Dangi', 'Deoni', 'Gir', 'Guernsey', 'Hallikar', 'Hariana', 'Holstein Friesian', 'Jaffarabadi', 'Jersey', 'Kangayam', 'Kankrej', 'Kasaragod', 'Kenkatha', 'Kherigarh', 'Khillari', 'Krishna Valley', 'Malnad Gidda', 'Mehsana', 'Murrah', 'Nagori', 'Nagpuri', 'Nili Ravi', 'Nimari', 'Ongole', 'Pulikulam', 'Rathi', 'Red Dane', 'Red Sindhi', 'Sahiwal', 'Surti', 'Tharparkar', 'Toda', 'Umblachery','Vechur']

        predictions = []
        for prob, idx in zip(top_probs[0], top_idxs[0]):
            if idx.item() < len(class_labels):
                label = class_labels[idx.item()]
            else:
                label = f"Unknown({idx.item()})"
            predictions.append({
                "breed": label,
                "accuracy": round(prob.item() * 100, 2)
            })

        image_file.seek(0) 
        upload_result = cloudinary.uploader.upload(
            image_file,
            folder="Model"
        )

        doc = {
            "url": upload_result.get("secure_url"),
            **metadata,
            "predictions": predictions
        }
        # result = collection.insert_one(doc)

        return build_response(
            201,
            "Image uploaded and predicted successfully",
            {
                # "id": str(result.inserted_id),
                "url": upload_result.get("secure_url"),
                "predictions": predictions
            }
        )

    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
