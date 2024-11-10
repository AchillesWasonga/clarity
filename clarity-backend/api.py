from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import base64
import os
from video import generate_manim_visualization

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/video")
async def create_video(question: str = Form(...)):
    video_path = generate_manim_visualization(question)
    if video_path:
        return FileResponse(video_path, media_type="video/mp4", filename="visualization.mp4")
    else:
        raise HTTPException(status_code=500, detail="Video generation failed")

# You can keep these functions if you need them for other purposes
def encode_image(image_path):
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
