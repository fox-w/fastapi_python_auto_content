import os
import tempfile
import requests
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
import numpy as np
import time

def analyze_video_format(clip):
    """
    Analyze video format and determine if it's social media ready.
    
    Args:
        clip: VideoFileClip object
    
    Returns:
        dict: Video analysis info
    """
    width, height = clip.size
    aspect_ratio = width / height
    
    # Define format categories
    if 0.5 <= aspect_ratio <= 0.6:  # 9:16 range (0.5625 is exact 9:16)
        format_type = "vertical_social"
        description = "Vertical (Social Media Ready)"
    elif 1.7 <= aspect_ratio <= 1.8:  # 16:9 range (1.777 is exact 16:9)
        format_type = "horizontal_standard"
        description = "Horizontal (Standard)"
    elif 0.9 <= aspect_ratio <= 1.1:  # Square-ish
        format_type = "square"
        description = "Square"
    elif aspect_ratio > 1.8:
        format_type = "ultra_wide"
        description = "Ultra-wide"
    else:
        format_type = "custom"
        description = "Custom aspect ratio"
    
    return {
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "format_type": format_type,
        "description": description,
        "is_social_ready": format_type == "vertical_social"
    }

def standardize_video_format(clips_info, target_format="auto"):
    """
    Determine the best output format based on input videos.
    
    Args:
        clips_info: List of video analysis dictionaries
        target_format: "auto", "vertical", "horizontal", or "keep_original"
    
    Returns:
        dict: Target format specifications
    """
    if target_format == "keep_original":
        # Use the format of the first video
        return {
            "width": clips_info[0]["width"],
            "height": clips_info[0]["height"],
            "format_type": clips_info[0]["format_type"],
            "resize_needed": False
        }
    
    elif target_format == "vertical":
        return {
            "width": 1080,
            "height": 1920,
            "format_type": "vertical_social",
            "resize_needed": True
        }
    
    elif target_format == "horizontal":
        return {
            "width": 1920,
            "height": 1080,
            "format_type": "horizontal_standard", 
            "resize_needed": True
        }
    
    else:  # auto mode
        # Count format types
        format_counts = {}
        for info in clips_info:
            fmt = info["format_type"]
            format_counts[fmt] = format_counts.get(fmt, 0) + 1
        
        # If majority are vertical/social, keep vertical
        if format_counts.get("vertical_social", 0) >= len(clips_info) / 2:
            return {
                "width": 1080,
                "height": 1920,
                "format_type": "vertical_social",
                "resize_needed": False  # Most are already correct
            }
        
        # If majority are horizontal, use horizontal
        elif format_counts.get("horizontal_standard", 0) >= len(clips_info) / 2:
            return {
                "width": 1920,
                "height": 1080,
                "format_type": "horizontal_standard",
                "resize_needed": False
            }
        
        # Mixed formats - default to vertical for social media
        else:
            return {
                "width": 1080,
                "height": 1920,
                "format_type": "vertical_social",
                "resize_needed": True
            }

def resize_clip_if_needed(clip, target_format):
    """
    Resize clip only if dimensions don't match target.
    
    Args:
        clip: VideoFileClip object
        target_format: Target format dictionary
    
    Returns:
        VideoClip: Resized clip if needed, original if not
    """
    current_width, current_height = clip.size
    target_width, target_height = target_format["width"], target_format["height"]
    
    if current_width != target_width or current_height != target_height:
        print(f"  Resizing from {current_width}x{current_height} to {target_width}x{target_height}")
        return clip.resized((target_width, target_height))
    else:
        print(f"  No resize needed - already {current_width}x{current_height}")
        return clip

def apply_dark_moody_effect(clip, intensity=0.7):
    """
    Apply a dark, moody effect to a video clip.
    
    Args:
        clip: VideoFileClip object
        intensity (float): How strong the effect is (0.0 to 1.0)
                          0.0 = no effect, 1.0 = maximum effect
    
    Returns:
        VideoClip with dark moody effect applied
    """
    def color_effect(frame):
        # Convert to grayscale first (for that black/white moody look)
        # Standard formula: 0.299*R + 0.587*G + 0.114*B
        gray = np.dot(frame[...,:3], [0.299, 0.587, 0.114])
        
        # Create a slightly blue-tinted grayscale (more cinematic)
        moody_frame = np.zeros_like(frame)
        moody_frame[:, :, 0] = gray * 0.9  # Red channel (slightly reduced)
        moody_frame[:, :, 1] = gray * 0.95 # Green channel 
        moody_frame[:, :, 2] = gray * 1.1  # Blue channel (slightly enhanced)
        
        # Darken the overall image
        moody_frame = moody_frame * (0.5 + 0.3 * (1 - intensity))
        
        # Increase contrast for more dramatic look
        moody_frame = ((moody_frame / 255.0 - 0.5) * (1 + intensity * 0.5) + 0.5) * 255
        
        # Blend with original based on intensity
        final_frame = frame * (1 - intensity) + moody_frame * intensity
        
        # Make sure values stay in valid range
        final_frame = np.clip(final_frame, 0, 255).astype(np.uint8)
        
        return final_frame
    
    return clip.image_transform(color_effect)

def download_media_from_url(url, file_extension=None):
    """
    Download media file from URL to a temporary file.
    
    Args:
        url (str): URL to download from
        file_extension (str): Expected file extension (e.g., 'mp4', 'mp3')
    
    Returns:
        str: Path to the downloaded temporary file
    """
    try:
        print(f"Downloading from URL: {url}")
        
        # Add proper headers to avoid blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'video/mp4,video/*,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity',  # Disable compression to ensure complete download
            'Connection': 'keep-alive'
        }
        
        response = requests.get(url, stream=True, timeout=60, headers=headers)
        response.raise_for_status()
        
        # Get content length for verification
        content_length = response.headers.get('content-length')
        if content_length:
            content_length = int(content_length)
            print(f"Expected file size: {content_length / (1024*1024):.2f} MB")
        
        # Determine file extension
        if not file_extension:
            content_type = response.headers.get('content-type', '')
            if 'video/mp4' in content_type:
                file_extension = 'mp4'
            elif 'audio/mpeg' in content_type:
                file_extension = 'mp3'
            elif 'audio/wav' in content_type:
                file_extension = 'wav'
            else:
                # Try to extract from URL
                if url.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    file_extension = url.split('.')[-1].lower()
                elif url.lower().endswith(('.mp3', '.wav', '.m4a')):
                    file_extension = url.split('.')[-1].lower()
                else:
                    file_extension = 'mp4'  # Default to mp4
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=f".{file_extension}", delete=False) as temp_file:
            temp_path = temp_file.name
            
            # Download in chunks with progress tracking
            downloaded_size = 0
            chunk_size = 8192
            
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    temp_file.write(chunk)
                    downloaded_size += len(chunk)
            
            # Ensure all data is written to disk
            temp_file.flush()
            os.fsync(temp_file.fileno())
        
        # Additional sync - wait for OS to finish writing
        time.sleep(0.2)
        
        # Verify download completion
        actual_size = os.path.getsize(temp_path)
        print(f"Downloaded {actual_size / (1024*1024):.2f} MB to: {temp_path}")
        
        if content_length and actual_size != content_length:
            print(f"Warning: Size mismatch. Expected: {content_length}, Got: {actual_size}")
            # If there's a size mismatch, wait a bit more and check again
            time.sleep(1.0)
            final_size = os.path.getsize(temp_path)
            if final_size != actual_size:
                print(f"File size changed after wait: {actual_size} -> {final_size}")
                actual_size = final_size
        
        # Verify file is not empty and has minimum size
        if actual_size < 1024:  # Less than 1KB is suspicious for a video
            raise Exception(f"Downloaded file is too small ({actual_size} bytes). Possible incomplete download.")
        
        # Try to verify file integrity by attempting to read its header
        try:
            with open(temp_path, 'rb') as f:
                header = f.read(16)
                # Check for common video file signatures
                if file_extension == 'mp4':
                    # MP4 files should have ftyp box early in the file
                    f.seek(0)
                    first_64_bytes = f.read(64)
                    if b'ftyp' not in first_64_bytes and b'moov' not in first_64_bytes:
                        print("Warning: File may not be a valid MP4")
                        
                        # Try reading more of the file to check for MP4 headers
                        f.seek(0)
                        first_1kb = f.read(1024)
                        if b'ftyp' not in first_1kb and b'moov' not in first_1kb and b'mdat' not in first_1kb:
                            raise Exception("Downloaded file does not appear to be a valid MP4")
        except Exception as verify_error:
            print(f"Warning: Could not verify file integrity: {verify_error}")
        
        # Final file access test
        try:
            with open(temp_path, 'rb') as test_file:
                test_file.read(1024)  # Try to read first 1KB
            print(f"File access test passed for: {temp_path}")
        except Exception as access_error:
            raise Exception(f"Downloaded file is not accessible: {str(access_error)}")
        
        return temp_path
        
    except Exception as e:
        print(f"Error downloading from {url}: {e}")
        raise Exception(f"Failed to download media from URL: {str(e)}")

def create_seamless_video_compilation(video_urls, audio_url=None, output_path=None, 
                                    format_mode="vertical", apply_moody_effect=False,
                                    moody_intensity=0.7, video_audio_volume=0.8, 
                                    background_music_volume=0.3):
    """
    Create a seamless video compilation from video URLs with optional background music.
    
    Args:
        video_urls (list): List of video URLs to download and combine
        audio_url (str, optional): URL of background audio/music
        output_path (str, optional): Output path for the final video
        format_mode (str): "vertical", "horizontal", or "auto"
        apply_moody_effect (bool): Whether to apply dark moody effect
        moody_intensity (float): Intensity of moody effect (0.0-1.0)
        video_audio_volume (float): Volume level for original video audio (0.0-1.0)
        background_music_volume (float): Volume level for background music (0.0-1.0)
    
    Returns:
        str: Path to the created video file
    """
    print(f"Creating seamless video compilation from {len(video_urls)} videos...")
    
    # Create output path if not provided
    if not output_path:
        output_path = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
    
    downloaded_videos = []
    downloaded_audio = None
    
    try:
        # Download all video files
        print("Downloading video files...")
        for i, video_url in enumerate(video_urls):
            print(f"Downloading video {i+1}/{len(video_urls)}")
            video_path = download_media_from_url(video_url, 'mp4')
            downloaded_videos.append(video_path)
        
        # Download background audio if provided
        if audio_url:
            print("Downloading background audio...")
            downloaded_audio = download_media_from_url(audio_url, 'mp3')
        
        # Load all video clips
        clips = []
        clips_info = []
        
        for i, video_path in enumerate(downloaded_videos):
            print(f"Loading video clip {i+1}/{len(downloaded_videos)}...")
            
            # Longer delay to ensure file is fully written
            time.sleep(1.0)  # Increased from 0.5 to 1.0 second
            
            # Verify file still exists and is accessible
            if not os.path.exists(video_path):
                raise Exception(f"Downloaded video file not found: {video_path}")
            
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                raise Exception(f"Downloaded video file is empty: {video_path}")
            
            print(f"  Loading file: {os.path.basename(video_path)} ({file_size / (1024*1024):.2f} MB)")
            
            # Add additional file stability check
            initial_size = file_size
            time.sleep(0.5)  # Wait a bit more
            final_size = os.path.getsize(video_path)
            
            if initial_size != final_size:
                print(f"  Warning: File size changed during wait ({initial_size} -> {final_size})")
                time.sleep(1.0)  # Wait even longer
                final_size = os.path.getsize(video_path)
            
            print(f"  File appears stable at {final_size / (1024*1024):.2f} MB")
            
            # Try multiple times to load the video with different approaches
            clip = None
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    print(f"  Attempt {attempt + 1}/{max_retries} to load video...")
                    
                    # Try loading with different threading settings
                    if attempt == 0:
                        # First attempt: normal loading
                        clip = VideoFileClip(video_path)
                    elif attempt == 1:
                        # Second attempt: with audio disabled first
                        clip = VideoFileClip(video_path, audio=False)
                        print(f"    Loaded without audio, duration: {clip.duration:.2f}s")
                        # Now try to add audio back
                        try:
                            clip_with_audio = VideoFileClip(video_path)
                            if clip_with_audio.audio is not None:
                                clip.close()
                                clip = clip_with_audio
                                print(f"    Successfully added audio back")
                        except:
                            print(f"    Keeping video without audio")
                    else:
                        # Third attempt: force reload with verbose output
                        clip = VideoFileClip(video_path, verbose=False, audio=False)
                    
                    # Verify the clip is valid by checking basic properties
                    if clip.duration <= 0:
                        clip.close()
                        raise Exception(f"Video clip has invalid duration: {clip.duration}")
                    
                    # Test reading the first frame
                    try:
                        first_frame = clip.get_frame(0)
                        print(f"  Successfully read first frame: {first_frame.shape}")
                    except Exception as frame_error:
                        print(f"  Warning: Could not read first frame: {frame_error}")
                        if attempt == max_retries - 1:
                            raise frame_error
                        clip.close()
                        continue
                    
                    print(f"  Successfully loaded: {clip.duration:.2f}s duration")
                    break
                    
                except Exception as clip_error:
                    print(f"  Attempt {attempt + 1} failed: {clip_error}")
                    if clip:
                        clip.close()
                        clip = None
                    
                    if attempt == max_retries - 1:
                        # Final attempt failed
                        print(f"  All attempts failed for video clip {i+1}")
                        # Clean up any existing clips before re-raising
                        for existing_clip in clips:
                            existing_clip.close()
                        raise Exception(f"Failed to load video clip {i+1} after {max_retries} attempts: {str(clip_error)}")
                    
                    # Wait before retry
                    time.sleep(1.0)
            
            clips.append(clip)
            
            # Analyze format
            info = analyze_video_format(clip)
            clips_info.append(info)
            print(f"  Format: {info['description']} ({info['width']}x{info['height']})")
        
        # Determine target format
        target_format = standardize_video_format(clips_info, format_mode)
        print(f"Target format: {target_format['format_type']} ({target_format['width']}x{target_format['height']})")
        
        # Resize clips if needed and apply effects
        processed_clips = []
        for i, clip in enumerate(clips):
            print(f"Processing clip {i+1}/{len(clips)}...")
            
            # Resize if needed
            processed_clip = resize_clip_if_needed(clip, target_format)
            
            # Apply moody effect if requested
            if apply_moody_effect:
                print(f"  Applying moody effect (intensity: {moody_intensity})")
                processed_clip = apply_dark_moody_effect(processed_clip, moody_intensity)
            
            processed_clips.append(processed_clip)
        
        # Concatenate clips seamlessly
        print("Concatenating clips...")
        final_video = concatenate_videoclips(processed_clips, method="compose")
        
        # Add background music if provided
        if downloaded_audio:
            print("Adding background music...")
            background_audio = AudioFileClip(downloaded_audio)
            
            # Loop background music to match video duration if needed
            if background_audio.duration < final_video.duration:
                loops_needed = int(final_video.duration / background_audio.duration) + 1
                background_audio = concatenate_audioclips([background_audio] * loops_needed)
            
            # Trim to match video duration
            background_audio = background_audio.subclipped(0, final_video.duration)
            
            # Mix audio with proper volume levels
            if final_video.audio:
                print(f"Mixing audio - Video: {int(video_audio_volume*100)}%, Background: {int(background_music_volume*100)}%")
                original_audio = final_video.audio.with_volume_scaled(video_audio_volume)
                mixed_audio = CompositeAudioClip([original_audio, background_audio.with_volume_scaled(background_music_volume)])
            else:
                mixed_audio = background_audio.with_volume_scaled(background_music_volume)
            
            final_video = final_video.with_audio(mixed_audio)
        
        # Export final video
        print(f"Exporting final video...")
        print(f"Duration: {final_video.duration:.2f} seconds")
        print(f"Resolution: {final_video.size[0]}x{final_video.size[1]}")
        print(f"Output: {output_path}")
        
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        # Cleanup
        for clip in clips + processed_clips:
            clip.close()
        final_video.close()
        
        print("Video compilation completed!")
        return output_path
        
    except Exception as e:
        print(f"Error creating video compilation: {e}")
        raise
    
    finally:
        # Clean up downloaded files
        print("Cleaning up temporary files...")
        for video_path in downloaded_videos:
            if os.path.exists(video_path):
                os.unlink(video_path)
        
        if downloaded_audio and os.path.exists(downloaded_audio):
            os.unlink(downloaded_audio)

if __name__ == "__main__":
    print("Simple Video Combiner")
    print("=" * 30)
    
    # Check input directory
    input_dir = "input_videos"
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"Created {input_dir} directory")
        print("Please add two video files and run again.")
        exit()
    
    # List available videos
    video_files = [f for f in os.listdir(input_dir) 
                   if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
    
    if len(video_files) < 2:
        print(f"Found {len(video_files)} video files in {input_dir}")
        print("Please add at least 2 video files:")
        print("- video1.mp4")
        print("- video2.mp4")
        exit()
    
    print(f"Found {len(video_files)} video files:")
    for i, video in enumerate(video_files):
        print(f"{i+1}. {video}")
    
    # Let user choose which videos to combine
    try:
        choice1 = int(input("\nSelect first video (number): ")) - 1
        choice2 = int(input("Select second video (number): ")) - 1
        
        if choice1 < 0 or choice1 >= len(video_files):
            print("Invalid first video choice")
            exit()
        if choice2 < 0 or choice2 >= len(video_files):
            print("Invalid second video choice")
            exit()
            
        video1_path = os.path.join(input_dir, video_files[choice1])
        video2_path = os.path.join(input_dir, video_files[choice2])
        
        output_name = input("Enter output filename (default: combined_video.mp4): ").strip()
        if not output_name:
            output_name = "combined_video.mp4"
        
        # Ensure the filename has a video extension
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
        if not any(output_name.lower().endswith(ext) for ext in video_extensions):
            print(f"Adding .mp4 extension to filename: {output_name}")
            output_name += ".mp4"
        
        output_dir = "output_videos"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_path = os.path.join(output_dir, output_name)
        
        # Ask about dark moody effects
        print("\nDark Moody Effects:")
        print("This will make your videos darker, more grayscale, and cinematic")
        apply_effects = input("Apply dark moody effects? (y/n): ").strip().lower() == 'y'
        
        effect_intensity = 0.7  # Default
        if apply_effects:
            try:
                intensity_input = input("Effect intensity (0.0-1.0, default 0.7): ").strip()
                if intensity_input:
                    effect_intensity = float(intensity_input)
                    effect_intensity = max(0.0, min(1.0, effect_intensity))  # Clamp between 0-1
            except ValueError:
                print("Invalid intensity, using default 0.7")
        
        # Ask about format handling
        print("\nFormat Handling:")
        print("How should we handle different video formats?")
        print("1. Auto (smart detection - recommended)")
        print("2. Force vertical (1080x1920 for social media)")
        print("3. Force horizontal (1920x1080 for standard)")
        print("4. Keep original (use first video's format)")
        
        format_choice = input("Choose format mode (1-4, default 1): ").strip()
        
        format_modes = {
            "1": "auto",
            "2": "vertical", 
            "3": "horizontal",
            "4": "keep_original"
        }
        
        format_mode = format_modes.get(format_choice, "auto")
        
        # Combine the videos
        combine_two_videos(video1_path, video2_path, output_path, apply_effects, effect_intensity, format_mode)
        
    except ValueError:
        print("Please enter valid numbers for video selection")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc() 