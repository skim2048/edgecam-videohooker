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

SERVER_INFO = ['main:app', '0.0.0.0', 12921]
ALLOWED_CORS = []


def get_videowriter(cfg):
    width = cfg.width
    height = cfg.height
    fps = cfg.fps
    bitrate = cfg.bitrate
    preset = cfg.preset
    keyint = cfg.keyint
    profile = cfg.profile
    location = cfg.location
    pipeline= (
        "appsrc ! videoconvert ! "
        f"video/x-raw,format=I420,width={width},height={height},framerate={fps}/1 ! "
        f"x264enc speed-preset={preset} bitrate={bitrate} key-int-max={keyint} ! "
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
    allow_origins=ALLOWED_CORS,
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
        SERVER_INFO[0],
        host=SERVER_INFO[1],
        port=SERVER_INFO[2]
    )