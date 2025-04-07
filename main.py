import json
from contextlib import asynccontextmanager

import cv2
from loguru import logger
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.capture import VideoCapture
from src.task import SingleThreadTask


class VideoHooker:

    def __init__(self):
        self._capture = VideoCapture()
        self._writer = cv2.VideoWriter()
        self._hooking_task = SingleThreadTask()

    def _hooking(self):
        frame = self._capture.read()
        self._writer.write(frame)
        logger.debug("Frame written to the server.")

    def hook(self, source, writer, api_preference=cv2.CAP_ANY):
        if not writer.isOpened():
            logger.warning("VideoWriter is not opened.")
            return
        self.stop()
        self._capture.open(source, api_preference)
        self._writer = writer
        self._hooking_task.start(self._hooking)

    def stop(self):
        if self._hooking_task.is_alive():
            self._hooking_task.stop()
        self._writer.release()
        self._capture.close()


class PipelineConfig(BaseModel):
    source: str
    width: int
    height: int
    fps: int
    bitrate: int
    speed_preset: str
    key_int_max: int
    profile: str
    location: str


VIDEO_HOOKER = VideoHooker()
PIPELINE_CONFIG = None

with open("settings.json", 'r') as f:
    SETTINGS = json.load(f)


def get_videowriter(cfg):
    width = cfg.width
    height = cfg.height
    fps = cfg.fps
    bitrate = cfg.bitrate
    speed_preset = cfg.speed_preset
    key_int_max = cfg.key_int_max
    profile = cfg.profile
    location = cfg.location
    pipeline= (
        "appsrc ! videoconvert ! "
        f"video/x-raw,format=I420,width={width},height={height},framerate={fps}/1 ! "
        f"x264enc speed-preset={speed_preset} bitrate={bitrate} key-int-max={key_int_max} ! "
        f"video/x-h264,profile={profile} ! "
        f"rtspclientsink location={location}"
    )
    return cv2.VideoWriter(pipeline, cv2.CAP_GSTREAMER, 0, fps, (width, height))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 「TODO: START
    # TODO: END」
    yield
    # 「TODO: START
    VIDEO_HOOKER.stop()
    # TODO: END」


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=SETTINGS["allowed_cors"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],)


@app.post('/hook/start')
async def start_hooking(cfg: PipelineConfig):
    print(cfg)
    try:
        writer = get_videowriter(cfg)
        VIDEO_HOOKER.hook(cfg.source, writer)
        return {"status": "hooking started."}
    except Exception as e:
        VIDEO_HOOKER.stop()
        raise HTTPException(status_code=500, detail=str(e))


@app.post('/hook/stop')
async def stop_hooking():
    try:
        VIDEO_HOOKER.stop()
        return {"status": "hooking stopped."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app=SETTINGS["app"],
        host=SETTINGS["host"],
        port=SETTINGS["port"]
    )
