from flask import Flask, request, jsonify
import time
import gc
from pymongo import MongoClient, errors
from dotenv import load_dotenv
import os
from datetime import datetime
from PIL import Image
import torch
import torch.nn as nn
import io
from torchvision import transforms, models
import torch.nn.functional as F
from bson import ObjectId

load_dotenv()

app = Flask(__name__)

# ------------------ DATABASE CONFIG ------------------
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "mockDB")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mockCollection")

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    breed_collection = db["Breed"]
    print("MongoDB connection successful.")
except errors.ConnectionFailure as e:
    print(f"MongoDB connection failed: {e}")
    collection = None
    breed_collection = None

# ------------------ CLASS LABELS ------------------
class_labels = [
    'Alambadi', 'Amritmahal', 'Ayrshire', 'Banni', 'Bargur', 'Bhadawari',
    'Brown Swiss', 'Dangi', 'Deoni', 'Gir', 'Guernsey', 'Hallikar', 'Hariana',
    'Holstein Friesian', 'Jaffarabadi', 'Jersey', 'Kangayam', 'Kankrej',
    'Kasaragod', 'Kenkatha', 'Kherigarh', 'Khillari', 'Krishna Valley',
    'Malnad Gidda', 'Mehsana', 'Murrah', 'Nagori', 'Nagpuri', 'Nili Ravi',
    'Nimari', 'Ongole', 'Pulikulam', 'Rathi', 'Red Dane', 'Red Sindhi',
    'Sahiwal', 'Surti', 'Tharparkar', 'Toda', 'Umblachery', 'Vechur'
]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = models.resnet50(weights=None)
num_classes = len(class_labels)

num_ftrs = model.fc.in_features
model.fc = nn.Sequential(
    nn.Dropout(p=0.5),
    nn.Linear(num_ftrs, num_classes) 
)

model.load_state_dict(torch.load("best_breed_classifier_finetuned.pth", map_location=device))

model.to(device)

model.eval()
print(f"Model loaded successfully on {device}.")


preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

try:
    breed_docs = list(breed_collection.find({}, {"_id": 1, "BreedName": 1}))
    BREED_MAP = {doc["BreedName"]: str(doc["_id"]) for doc in breed_docs}
except Exception as e:
    print(f"Could not cache breeds from MongoDB: {e}")
    BREED_MAP = {}

def build_response(status_code, message, body=None):
    response_data = {
        "status_code": status_code,
        "message": message,
    }
    if body is not None:
        response_data["body"] = body
    return jsonify(response_data), status_code

# ------------------ API ROUTES ------------------

@app.route("/")
def home():
    return "Hello, Cattle Breed Identification API is running!"

@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        if not data or "user_id" not in data or "password" not in data:
            return build_response(400, "user_id and password are required")

        user_id = data["user_id"]
        password = data["password"]

        existing_user = collection.find_one({"user_id": user_id})
        if existing_user:
            existing_user["_id"] = str(existing_user["_id"])
            existing_user.pop("password", None)
            existing_user.pop("cattles", None)
            return build_response(200, "Login successful", existing_user)

        result = collection.insert_one({"user_id": user_id, "password": password})
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
            return build_response(400, "No data provided")

        required_fields = ["user_id", "tag_number", "species", "breed"]
        for field in required_fields:
            if field not in data:
                return build_response(400, f"Missing required field: {field}")

        user_id = data["user_id"]
        breed_name = data["breed"]

        user = collection.find_one({"user_id": user_id})
        if not user:
            return build_response(404, "User not found")

        breed_id = BREED_MAP.get(breed_name)
        if not breed_id:
            return build_response(404, f"Breed '{breed_name}' not found in cache")

        cattle_doc = {
            "name": data.get("name"),
            "tag_number": data["tag_number"],
            "data_entry_date": data.get("data_entry_date", datetime.utcnow().strftime("%Y-%m-%d")),
            "tagging_date": data.get("tagging_date"),
            "species": data["species"],
            "sex": data.get("sex"),
            "dob": data.get("dob"),
            "breed_id": breed_id,
            "breed_name": breed_name
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
                "breed_id": breed_id,
                "breed_name": breed_name
            }
        )
    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})

@app.route("/get-cattle", methods=["GET"])
def get_cattle():
    try:
        user_id = request.args.get("userId")
        if not user_id:
            return build_response(400, "userId is required as a query parameter")

        user = collection.find_one({"user_id": user_id}, {"_id": 0, "cattles": 1})
        if not user:
            return build_response(404, "User not found")

        return build_response(200, "Cattle data fetched successfully", user.get("cattles", []))
    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})

@app.route("/get-breed/<breed_id>", methods=["GET"])
def get_breed(breed_id):
    try:
        if not ObjectId.is_valid(breed_id):
            return build_response(400, "Invalid breed_id format")

        breed = breed_collection.find_one({"_id": ObjectId(breed_id)}, {"_id": 0})
        if not breed:
            return build_response(404, "Breed not found")

        return build_response(200, "Breed fetched successfully", breed)
    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})

@app.route("/upload-and-predict", methods=["POST"])
def upload_and_predict():
    try:
        start_total = time.time()
        if "image" not in request.files:
            return build_response(400, "No image file provided")

        image_file = request.files["image"]
        img_bytes = image_file.read()
        
        start_preprocess = time.time()
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        input_tensor = preprocess(image).unsqueeze(0).to(device)
        preprocess_time = time.time() - start_preprocess

        start_infer = time.time()
        with torch.no_grad():
            output = model(input_tensor)
            probabilities = F.softmax(output, dim=1)
            top_probs, top_idxs = torch.topk(probabilities, 3)
        infer_time = time.time() - start_infer

        del output, probabilities, input_tensor
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

        top_breeds = [class_labels[idx.item()] for idx in top_idxs[0]]
        predictions = [
            {
                "breed": breed,
                "breed_id": BREED_MAP.get(breed),
                "accuracy": round(prob.item() * 100, 2)
            }
            for prob, breed in zip(top_probs[0], top_breeds)
        ]

        total_time = time.time() - start_total
        timing_info = {
            "preprocess_time": round(preprocess_time, 3),
            "inference_time": round(infer_time, 3),
            "total_time": round(total_time, 3)
        }

        return build_response(201, "Prediction successful", {"predictions": predictions, "timing": timing_info})
    except Exception as e:
        return build_response(500, "Internal Server Error", {"error": str(e)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)