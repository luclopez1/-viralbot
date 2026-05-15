import os, subprocess

ffmpeg_bin = r"C:\ffmpeg\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe"
srt_path = "temp/voice.srt"
srt_abs = os.path.abspath(srt_path).replace("\\", "/")
drive = srt_abs[0]
srt_ffmpeg = drive + "\\:" + srt_abs[2:]
print("SRT path para FFmpeg:", srt_ffmpeg)

sub_filter = f"subtitles='{srt_ffmpeg}':force_style='FontSize=18,FontName=Arial,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,Shadow=1,Alignment=2,MarginV=80'"
last_video = sorted(os.listdir("videos_output"))[-1]
cmd = [ffmpeg_bin, "-y", "-i", f"videos_output/{last_video}", "-vf", sub_filter, "-c:v", "libx264", "-preset", "fast", "-c:a", "copy", "videos_output/test_subs.mp4"]

result = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", result.returncode)
print("STDERR:", result.stderr[-800:] if result.stderr else "none")
