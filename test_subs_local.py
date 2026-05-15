import subprocess, os, shutil

ffmpeg_bin = r"C:\ffmpeg\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe"

# Copy SRT locally
shutil.copy("temp/voice.srt", "subs_temp.srt")
print("SRT exists:", os.path.exists("subs_temp.srt"))

# Show first few lines of SRT
with open("subs_temp.srt", "r", encoding="utf-8") as f:
    print("SRT content preview:")
    print(f.read()[:300])

# Get last video
videos = sorted([f for f in os.listdir("videos_output") if f.endswith(".mp4") and "nosubs" not in f and "test" not in f])
if not videos:
    print("No videos found")
    exit(1)
last_video = videos[-1]
print(f"\nUsing video: {last_video}")

# Try subtitles filter with local path
sub_filter = "subtitles=subs_temp.srt:force_style='FontSize=18,FontName=Arial,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,Shadow=1,Alignment=2,MarginV=80'"
cmd = [ffmpeg_bin, "-y", "-i", f"videos_output/{last_video}", "-vf", sub_filter,
       "-c:v", "libx264", "-preset", "fast", "-c:a", "copy", "videos_output/test_subs_local.mp4"]
print("\nRunning FFmpeg...")
result = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
print("Return code:", result.returncode)
if result.returncode != 0:
    print("STDERR last 800:")
    print(result.stderr[-800:])

    # Try alternative: convert SRT to ASS first, then use ass filter
    print("\n--- Trying ASS approach ---")
    cmd_convert = [ffmpeg_bin, "-y", "-i", "subs_temp.srt", "subs_temp.ass"]
    r = subprocess.run(cmd_convert, capture_output=True, text=True, errors="replace")
    print("Convert to ASS:", r.returncode)
    if r.returncode == 0:
        cmd_ass = [ffmpeg_bin, "-y", "-i", f"videos_output/{last_video}",
                   "-vf", "ass=subs_temp.ass",
                   "-c:v", "libx264", "-preset", "fast", "-c:a", "copy",
                   "videos_output/test_subs_ass.mp4"]
        r2 = subprocess.run(cmd_ass, capture_output=True, text=True, errors="replace")
        print("ASS burn returncode:", r2.returncode)
        if r2.returncode != 0:
            print("STDERR:", r2.stderr[-600:])
        else:
            print("SUCCESS with ASS filter!")
else:
    print("SUCCESS with subtitles filter!")
