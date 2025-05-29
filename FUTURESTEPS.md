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
