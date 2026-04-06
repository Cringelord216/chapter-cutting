import os
import json
import subprocess

# --- CONFIGURATION ---
# Test this on a single season folder first!
MEDIA_DIRECTORY = r"D:\TV Shows\Supernatural\Season 1" 

#Make sure to download and install ffprobe
FFPROBE_PATH = r"C:\ffmpeg\bin\ffprobe.exe"
FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"

# 0 = Cuts only the Recap (Plex Chapter 1)
# 1 = Cuts the Recap AND the Intro (Plex Chapter 2)
CHAPTER_INDEX_TO_CUT = 0 

def get_chapter_end_time(filepath):
    """Extracts the exact end time (in seconds) of the target chapter."""
    cmd = [
        FFPROBE_PATH, 
        '-v', 'error',
        '-print_format', 'json',
        '-show_chapters', 
        filepath
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        info = json.loads(result.stdout)
        
        chapters = info.get('chapters', [])
        
        # Ensure the file actually has enough chapters to make the cut
        if len(chapters) > CHAPTER_INDEX_TO_CUT:
            # We want the time in SECONDS for ffmpeg, not milliseconds
            return float(chapters[CHAPTER_INDEX_TO_CUT].get('end_time', 0))
            
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return None

def trim_video(input_path, output_path, start_time):
    """Uses FFmpeg to stream-copy the video starting from the target time."""
    cmd = [
        FFMPEG_PATH,
        '-ss', str(start_time), # Seek to this time
        '-i', input_path,       # The input file
        '-c', 'copy',           # Copy the video/audio streams without re-encoding
        '-map', '0',            # Keep all tracks (audio, video, subtitles)
        output_path             # The new output file
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"Error cutting {input_path}: {e}")
        return False

def main():
    print(f"Scanning directory tree: {MEDIA_DIRECTORY}...")

    for root, dirs, files in os.walk(MEDIA_DIRECTORY):
        # Prevent the script from processing the "Trimmed" folders it creates
        if "Trimmed" in root:
            continue

        for filename in files:
            if not filename.endswith(('.mkv', '.mp4', '.avi')):
                continue

            input_filepath = os.path.join(root, filename)
            print(f"\nAnalyzing: {filename}")
            
            cut_time_sec = get_chapter_end_time(input_filepath)

            if cut_time_sec:
                # Create a "Trimmed" folder inside the current directory
                output_folder = os.path.join(root, "Trimmed")
                os.makedirs(output_folder, exist_ok=True)
                
                output_filepath = os.path.join(output_folder, filename)
                
                print(f"  -> Cutting first {cut_time_sec} seconds...")
                success = trim_video(input_filepath, output_filepath, cut_time_sec)
                
                if success:
                    print(f"Success! Saved to Trimmed folder.")
                else:
                    print(f"Failed to cut video.")
            else:
                print(f"No chapter data found to cut.")

    print("\nFinished processing all files.")

if __name__ == "__main__":
    main()
