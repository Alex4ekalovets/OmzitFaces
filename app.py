import base64
import json
import logging
from multiprocessing import Process, Queue, Array

from pydantic import BaseModel

import settings
from jinja2.filters import FILTERS
from sqlalchemy.orm import Session

from settings import SOURCES, sources_settings

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from main import start_in_process
from utils.db import Detection, engine, EmployeePhoto

app = FastAPI()

FILTERS['b64encode'] = lambda x: base64.b64encode(x).decode("utf-8")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

PROCESSES = dict()


class CreateSettings(BaseModel):
    video_source: str
    crop: list[int | None] = (None, None, None, None)


class StartSettings(BaseModel):
    unknown_save_step: int = 10
    width: int = 1024
    skipped_frames_coeff: int = 50
    faces_distance: float = 0.6
    intervals: list[str] | None = None


class StreamSettings(BaseModel):
    is_record: bool = False
    is_recognized: bool = False


class VideoSettings(BaseModel):
    create: CreateSettings
    start: StartSettings
    stream: StreamSettings


def image_file_to_bytes(image_path):
    try:
        with open(image_path, 'rb') as img:
            img = img.read()
            img = bytearray(img)
            img = b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + img + b'\r\n'
            return img
    except Exception as ex:
        logging.exception(ex)


def stop_process(source_name):
    PROCESSES[source_name]['process'].kill()
    PROCESSES[source_name]['queue'].close()


def start_process(source_name):
    PROCESSES[source_name] = {
        'queue': Queue(),
        'crop': Array('i', range(4))
    }
    proc = Process(
        target=start_in_process,
        args=(source_name, PROCESSES[source_name]['queue'], PROCESSES[source_name]['crop'])
    )
    PROCESSES[source_name]['process'] = proc
    proc.start()


for source in SOURCES.keys():
    start_process(source)


def frame_gen(source_name):
    loading_img = image_file_to_bytes('static/img/loading.gif')
    no_video_img = image_file_to_bytes('static/img/no-video.png')
    try:
        while True:
            if PROCESSES[source_name]['process'].is_alive():
                if PROCESSES[source_name]['crop'][1] != 1:
                    yield PROCESSES[source_name]['queue'].get()
                else:
                    yield loading_img
            else:
                yield no_video_img
    except GeneratorExit:
        logging.debug('Generator exit')


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/sources")
def sources():
    return list(SOURCES.keys())


@app.get("/video_settings/{source_name}")
def video_settings(source_name: str):
    SOURCES[source_name]['create']['crop'] = PROCESSES[source_name]['crop'][:]
    return SOURCES[source_name]


@app.get("/video_stream/{source_name}")
def video_stream(source_name: str):
    return StreamingResponse(content=frame_gen(source_name), media_type="multipart/x-mixed-replace;boundary=frame")


@app.get("/play_video/{source_name}")
def play_video(source_name: str):
    start_process(source_name)
    return


@app.get("/stop_video/{source_name}")
def stop_video(source_name: str):
    stop_process(source_name)
    return


@app.post("/video_settings/{source_name}")
async def video_settings(source_name: str, settings: VideoSettings):
    SOURCES[source_name] = settings.dict()
    with open(sources_settings, 'w') as file:
        json.dump(SOURCES, file)
    stop_process(source_name)
    start_process(source_name)
    return


@app.get('/detections', response_class=HTMLResponse)
async def detections(request: Request):
    with Session(autoflush=False, bind=engine) as db:
        query = db.query(Detection.datetime, Detection.id, Detection.photo, Detection.name, EmployeePhoto.department)
        query = query.join(EmployeePhoto, Detection.name == EmployeePhoto.name)
        context = {
            'detections': query,
        }
        return templates.TemplateResponse(request=request, name="tables.html", context=context)
