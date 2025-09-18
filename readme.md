# Mock API Documentation

This API provides endpoints for user registration, cattle management, breed fetching, and image uploads with ML-based breed prediction.

---

## **1. User Login / Registration**

* **URL:** `/login`  
* **Method:** `POST`  
* **Request Body:** JSON

```json
{
  "user_id": "string",
  "password": "string"
}
```

* **Description:** Registers a new user. Returns conflict if user already exists.  
* **Response:**

```json
{
  "status_code": 201,
  "message": "User registered successfully",
  "body": {
    "id": "mongo_inserted_id",
    "user_id": "user_id"
  }
}
```

---

## **2. Add Cattle**

* **URL:** `/push-cattle`  
* **Method:** `POST`  
* **Request Body:** JSON

```json
{
  "user_id": "string",
  "tag_number": "string",
  "species": "string",
  "breed": "string",
  "name": "string (optional)",
  "data_entry_date": "YYYY-MM-DD (optional)",
  "tagging_date": "YYYY-MM-DD (optional)",
  "sex": "string (optional)",
  "dob": "YYYY-MM-DD (optional)"
}
```

* **Description:** Adds a cattle entry to the user's `cattles` array.  
* **Response:**

```json
{
  "status_code": 201,
  "message": "Cattle added successfully",
  "body": {
    "user_id": "user_id",
    "tag_number": "tag_number",
    "breed_id": "mongo_object_id",
    "breed_name": "BreedName"
  }
}
```

---

## **3. Get Cattles**

* **URL:** `/get-cattle?userId=XXXX`  
  Example: `http://localhost:5000/get-cattle?userId=abhineet1243`  
* **Method:** `GET`  
* **Query Parameters:**

```text
userId=<user_id>
```

* **Description:** Fetches all cattle data for a given user.  
* **Response:**

```json
{
  "status_code": 200,
  "message": "Cattle data fetched successfully",
  "body": [
    {
      "name": "string",
      "tag_number": "string",
      "data_entry_date": "YYYY-MM-DD",
      "tagging_date": "YYYY-MM-DD",
      "species": "string",
      "sex": "string",
      "dob": "YYYY-MM-DD",
      "breed_id": "mongo_object_id",
      "breed_name": "string"
    }
  ]
}
```

---

## **4. Get Breed by ID**

* **URL:** `/get-breed/<breed_id>`  
* **Method:** `GET`  
* **Path Parameters:**

```text
breed_id = Mongo ObjectId
```

* **Description:** Fetches breed details from the `Breed` collection using its MongoDB ObjectId.  
* **Response:**

```json
{
  "status_code": 200,
  "message": "Breed fetched successfully",
  "body": {
    "BreedName": "string",
    "Description": "string",
    ...
  }
}
```

---

## **5. Upload & Predict Image**

* **URL:** `/upload-and-predict`  
* **Method:** `POST`  
* **Request:** `multipart/form-data`

  * **Fields:**
    * `image`: image file (**required**)  
    * `name`: string (optional)  
    * `description`: string (optional)  

* **Description:**  
  Uploads an image to Cloudinary, runs the ML model to classify the cattle/breed, and returns the **top 3 predictions with accuracies**.  

* **Response:**

```json
{
  "status_code": 201,
  "message": "Image uploaded and predicted successfully",
  "body": {
    "url": "cloudinary_image_url",
    "predictions": [
      {
        "breed": "Gir",
        "accuracy": 87.32
      },
      {
        "breed": "Sahiwal",
        "accuracy": 8.45
      },
      {
        "breed": "Hallikar",
        "accuracy": 4.23
      }
    ]
  }
}
```

---

## **Notes**

* All error responses follow the same format:

```json
{
  "status_code": <error_code>,
  "message": "<error_message>",
  "body": {
    "error": "error details"
  }
}
```

* Dates should follow `YYYY-MM-DD` format where applicable.
* The ML model currently supports **classification into 40+ breeds** (e.g., Gir, Sahiwal, Jersey, Holstein Friesian, etc.).

