---
title: FastAPI
description: A FastAPI server
tags:
  - fastapi
  - hypercorn
  - python
---

# FastAPI Example

This example starts up a [FastAPI](https://fastapi.tiangolo.com/) server.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/-NvLj4?referralCode=CRJ8FE)

# Quote Image Generator API

A simple FastAPI application that generates quote images and uploads them to Cloudinary.

## Features

- Generate beautiful quote images with customized text
- Support for bold text formatting using {word} syntax
- Support for line breaks using \n
- Automatic upload to Cloudinary
- Ready for deployment on Railway

## Deployment on Railway

This API is designed to be deployed on Railway. Just push to your repository and Railway will automatically build and deploy the application.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/-NvLj4?referralCode=CRJ8FE)

### Environment Variables

You need to set the following environment variables in your Railway project:

- `CLOUDINARY_CLOUD_NAME`: Your Cloudinary cloud name
- `CLOUDINARY_API_KEY`: Your Cloudinary API key
- `CLOUDINARY_API_SECRET`: Your Cloudinary API secret

## API Endpoints

### GET /

Returns a simple message to confirm the API is running.

### POST /generate

Generates a quote image and uploads it to Cloudinary.

**Request Body:**

```json
{
  "text": "Your {inspiring} quote text\nwith line breaks"
}
```

- Use `{word}` syntax for bold text
- Use `\n` for line breaks

**Response:**

```json
{
  "url": "https://res.cloudinary.com/your-cloud/image/upload/v1234567890/quote_images/quote_abcd1234.png",
  "public_id": "quote_images/quote_abcd1234"
}
```

## Local Development

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set environment variables for Cloudinary
4. Run the application:
   ```
   hypercorn main:app --reload
   ```

## Testing the API

You can test the API using curl:

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your {vision} is worthless\nwithout {relentless} execution."}'
```

Or use tools like Postman or Insomnia to send requests.

## ✨ Features

- FastAPI
- [Hypercorn](https://hypercorn.readthedocs.io/)
- Python 3

## 💁‍♀️ How to use

- Clone locally and install packages with pip using `pip install -r requirements.txt`
- Run locally using `hypercorn main:app --reload`

## 📝 Notes

- To learn about how to use FastAPI with most of its features, you can visit the [FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/)
- To learn about Hypercorn and how to configure it, read their [Documentation](https://hypercorn.readthedocs.io/)


# FUTURESTEPS.md

The biggest next step is to add the ability to generate videos. This will entail the following:

- [ ] **1. Create a barebones MVP for video creation** that can take in any number of clips, splice them together, and select a certain preconfigured style (that will determine the cuts between the clips, the hook, the soundtrack, the filter over the video, the cropping/frame around the video (like the rounded edges crop), etc.). The script should accept the number of clips, the names of the clips, and the soundtrack URL.

- [ ] **2. Transcript Overlay (optional):**
  - Accept a transcript with timestamps for each word associated with each clip.
  - Render synchronized text overlays on the video, aligned with the spoken words.

- [ ] **3. Add API endpoint** `/generate-sf-video/` in `main.py` for generating short-form videos. This endpoint will take inputs:
  - `video_urls: List[str]`
  - `audio_mp3_url: Optional[str]`
  - `style: int` (style ID, 1–N)

- [ ] **4. Deploy to Railway** using Docker or direct repo integration.

- [ ] **5. Test end-to-end**:
  - Use `curl` or PowerShell `Invoke-WebRequest` to invoke the `/generate-sf-video/` endpoint and verify the video output.

- [ ] **6. Storage & retention planning**:
  - Check the typical size of each generated video.
  - Determine available space on the Cloudinary account.
  - Plan automatic deletion or archiving rules to avoid exceeding account limits.

---

*Use this checklist to track and organize the next steps for implementing short-form video functionality.*
