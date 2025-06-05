# Seamless Video Generation API

This API endpoint allows you to create seamless video compilations from multiple video URLs with optional background music.

## Endpoint

**POST** `/generate-sf-videos`

## Features

- ✅ **URL-based video input**: Download videos directly from URLs
- ✅ **Seamless compilation**: Smooth transitions between clips (no hard cuts)
- ✅ **Background music**: Optional audio track mixing
- ✅ **Format control**: Vertical (Instagram/TikTok), horizontal, or auto-detect
- ✅ **Volume control**: Separate volume levels for video audio and background music
- ✅ **Visual effects**: Optional dark moody effect
- ✅ **Cloudinary upload**: Automatic upload and hosting

## Request Format

```json
{
  "video_urls": [
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4",
    "https://example.com/video3.mp4"
  ],
  "audio_url": "https://example.com/background_music.mp3",
  "format_mode": "vertical",
  "apply_moody_effect": true,
  "moody_intensity": 0.7,
  "video_audio_volume": 0.8,
  "background_music_volume": 0.3
}
```

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `video_urls` | `List[str]` | ✅ Yes | - | List of video URLs to combine (max 10) |
| `audio_url` | `str` | ❌ No | `null` | URL for background music/audio |
| `format_mode` | `str` | ❌ No | `"vertical"` | Output format: `"vertical"`, `"horizontal"`, or `"auto"` |
| `apply_moody_effect` | `bool` | ❌ No | `false` | Apply dark, cinematic visual effect |
| `moody_intensity` | `float` | ❌ No | `0.7` | Intensity of moody effect (0.0-1.0) |
| `video_audio_volume` | `float` | ❌ No | `0.8` | Volume level for original video audio (0.0-1.0) |
| `background_music_volume` | `float` | ❌ No | `0.3` | Volume level for background music (0.0-1.0) |

## Format Modes

- **`"vertical"`**: 1080x1920 (Instagram Stories, TikTok, YouTube Shorts)
- **`"horizontal"`**: 1920x1080 (YouTube, standard video)
- **`"auto"`**: Automatically detect based on input videos

## Response Format

```json
{
  "url": "https://res.cloudinary.com/your-cloud/video/upload/v1234567890/sf_videos/seamless_video_abcd1234.mp4",
  "public_id": "sf_videos/seamless_video_abcd1234"
}
```

Clean and simple! Just the essentials you need:
- **`url`**: Direct link to your processed video on Cloudinary
- **`public_id`**: Cloudinary identifier for managing the video

## Example Usage

### Basic Video Compilation

```bash
curl -X POST "http://localhost:8000/generate-sf-videos" \
  -H "Content-Type: application/json" \
  -d '{
    "video_urls": [
      "https://example.com/motivational1.mp4",
      "https://example.com/motivational2.mp4"
    ],
    "format_mode": "vertical"
  }'
```

### Full-Featured Request

```bash
curl -X POST "http://localhost:8000/generate-sf-videos" \
  -H "Content-Type: application/json" \
  -d '{
    "video_urls": [
      "https://example.com/david_goggins.mp4",
      "https://example.com/jocko_willink.mp4",
      "https://example.com/chris_williamson.mp4"
    ],
    "audio_url": "https://example.com/epic_music.mp3",
    "format_mode": "vertical",
    "apply_moody_effect": true,
    "moody_intensity": 0.7,
    "video_audio_volume": 0.8,
    "background_music_volume": 0.3
  }'
```

### Python Example

```python
import requests

response = requests.post(
    "http://localhost:8000/generate-sf-videos",
    json={
        "video_urls": [
            "https://example.com/video1.mp4",
            "https://example.com/video2.mp4"
        ],
        "audio_url": "https://example.com/music.mp3",
        "format_mode": "vertical",
        "video_audio_volume": 0.8,
        "background_music_volume": 0.3
    }
)

if response.status_code == 200:
    result = response.json()
    print(f"Video URL: {result['url']}")
else:
    print(f"Error: {response.status_code}")
```

## Audio Volume Guidelines

For **motivational videos** where speech clarity is important:
- **Video audio**: 0.8-1.0 (80-100%) - Keep speech loud and clear
- **Background music**: 0.2-0.4 (20-40%) - Subtle background enhancement

For **music-focused content**:
- **Video audio**: 0.6-0.8 (60-80%) - Moderate speech volume
- **Background music**: 0.4-0.6 (40-60%) - More prominent music

## Error Handling

The API returns appropriate HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid parameters)
- **500**: Server error (processing failed)

Example error response:
```json
{
  "detail": "At least one video URL is required"
}
```

## Limitations

- Maximum 10 videos per compilation
- 5-minute timeout for processing
- Requires valid video URLs (accessible without authentication)
- Supported video formats: MP4, AVI, MOV, MKV
- Supported audio formats: MP3, WAV, M4A

## Environment Variables

Make sure these Cloudinary environment variables are set:

```bash
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

## Running the API

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server:**
   ```bash
   hypercorn main:app --reload
   ```

3. **Test the endpoint:**
   ```bash
   python test_video_api.py
   ```

## Processing Time

Video processing time depends on:
- Number of videos
- Length of videos
- Video resolution
- Whether effects are applied
- Server resources

Typical processing times:
- 2-3 short clips (5-10 seconds each): 30-60 seconds
- 5-6 clips with background music: 1-3 minutes
- Large files or many clips: 3-5 minutes 