Got it! Here's a complete **README.md** for your API routes, all in one place:

```markdown
# Mock API with MongoDB & Cloudinary

This API provides endpoints to store JSON data, fetch it, and upload images with metadata. Built using **Flask**, **MongoDB**, and **Cloudinary**.

---

## Base URL

```

[http\://<your-server-ip>:<port>/](https://model-backend-oefv.onrender.com)

````

---

## API Routes

### 1. `POST /push`

Insert JSON data into MongoDB.

**Request:**

- **Headers:** `Content-Type: application/json`
- **Body Example:**

```json
{
  "name": "Abhineet Sahay",
  "role": "Student",
  "course": "Engineering"
}
````

**Response Example:**

```json
{
  "status_code": 201,
  "message": "Data inserted",
  "body": {
    "id": "6510a2f3b1c1234567890abc"
  }
}
```

**Error Responses:**

* `400` → No data provided
* `500` → Internal Server Error

---

### 2. `GET /get`

Fetch all data from the MongoDB collection.

**Request:** No body required.

**Response Example:**

```json
{
  "status_code": 200,
  "message": "Data fetched successfully",
  "body": [
    {
      "name": "Abhineet Sahay",
      "role": "Student",
      "course": "Engineering"
    },
    {
      "name": "John Doe",
      "role": "Teacher",
      "course": "Math"
    }
  ]
}
```

**Error Responses:**

* `500` → Internal Server Error
* If no data found:

```json
{
  "status_code": 200,
  "message": "No data found",
  "body": []
}
```

---

### 3. `POST /upload-image`

Upload an image to Cloudinary and store metadata in MongoDB.

**Request:**

* **Headers:** `Content-Type: multipart/form-data`
* **Form Data:**

  * `image` → The image file to upload (required)
  * `name` → Optional name metadata
  * `description` → Optional description metadata

**Example using `curl`:**

```bash
curl -X POST http://<server-ip>:5000/upload-image \
  -F "image=@/path/to/image.jpg" \
  -F "name=Sample Image" \
  -F "description=This is a test image"
```

**Response Example:**

```json
{
  "status_code": 201,
  "message": "Image uploaded successfully",
  "body": {
    "id": "6510a3f7b1c1234567890def",
    "url": "https://res.cloudinary.com/demo/image/upload/v1234567890/Model/image.jpg"
  }
}
```

**Error Responses:**

* `400` → No image file provided
* `500` → Internal Server Error

---

## Notes

* Make sure **MongoDB URI**, **DB name**, **Collection name**, and **Cloudinary credentials** are properly set in `.env`.
* All responses follow the format:

```json
{
  "status_code": <int>,
  "message": "<string>",
  "body": <object|array|null>
}
```

```

If you want, I can also **add example Postman requests** for all three routes so someone can test it instantly. Do you want me to do that?
```
