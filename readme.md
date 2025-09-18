````markdown
# Mock API Documentation

This API provides endpoints for user registration, cattle management, breed fetching, and image uploads.

---

## **1. Push Data**
- **URL:** `/push`  
- **Method:** `POST`  
- **Request Body:** JSON  
```json
{
  "key": "value",
  ...
}
````

* **Description:** Insert arbitrary data into the default collection.
* **Response:**

```json
{
  "status_code": 201,
  "message": "Data inserted",
  "body": {
    "id": "mongo_inserted_id"
  }
}
```

---

## **2. User Login / Registration**

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

## **3. Add Cattle**

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
  "message": "Cattle added successfully to user",
  "body": {
    "user_id": "user_id",
    "tag_number": "tag_number",
    "breed_id": "mongo_object_id",
    "breed_name": "BreedName"
  }
}
```

---

## **4. Get Cattles**

* **URL:** `/get-cattle`
http://localhost:5000/get-cattle?userId=abhineet1243

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
    },
    ...
  ]
}
```

---

## **5. Get Breed by ID**

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

## **6. Upload Image**

* **URL:** `/upload-image`
* **Method:** `POST`
* **Request:** `multipart/form-data`

  * **Fields:**

    * `image`: image file (required)
    * `name`: string (optional)
    * `description`: string (optional)
* **Description:** Uploads an image to Cloudinary and stores metadata in the collection.
* **Response:**

```json
{
  "status_code": 201,
  "message": "Image uploaded successfully",
  "body": {
    "id": "mongo_inserted_id",
    "url": "cloudinary_image_url"
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

```

I can also make a **more compact table version** that lists all routes with their method, request, and response in one glance. It’s easier for quick reference.  

Do you want me to do that too?
```
