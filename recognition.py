import datetime
import logging
import os
import pickle
import time
from math import ceil
from threading import Thread
from typing import Dict, Tuple, Optional

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from insightface.app.common import Face
from tqdm import tqdm

from settings import DATA_PATH
from utils.cv import (add_logo, add_name, add_source_photo, add_datetime, cv_image_to_bytes, bytes_to_cv)
from scipy import spatial

from utils.db import sync_db_with_scud, create, Detection

logger = logging.getLogger("logger")


class InsightFace:
    def __init__(self, video_source=0, crop=(None, None, None, None), db_path=DATA_PATH):
        self.stop = True
        self.record = False
        self.app = FaceAnalysis(name="buffalo_l", providers=['CPUExecutionProvider'])
        self.app.prepare(ctx_id=0, det_thresh=0.7, det_size=(256, 256))
        self.video_source = video_source
        self.db_path = db_path
        self.encodings = self.get_or_create_encodings()
        if not self.encodings:
            thread = Thread(target=self.retry_creation_encodings)
            thread.start()
        self.detected_faces = dict()
        try:
            self.video_capture = cv2.VideoCapture(self.video_source)
        except Exception as ex:
            logger.debug(ex)

        self.crop = self.get_crop(crop)

    def get_crop(self, crop):
        if self.video_capture.isOpened():
            x0 = crop[2] if crop[2] else 0
            y0 = crop[0] if crop[0] else 0
            x1 = crop[3] if crop[3] else int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            y1 = crop[1] if crop[1] else int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return y0, y1, x0, x1

    def retry_creation_encodings(self):
        current_stop_state = self.stop
        while not self.encodings:
            self.stop = True
            logger.info('Попытка повторного подключения к СКУД и получения кодировок...')
            time.sleep(3)
            self.encodings = self.get_or_create_encodings()
        else:
            self.stop = current_stop_state

    def get_or_create_encodings(self):
        encodings_path = os.path.join(self.db_path, 'enc')
        employees = sync_db_with_scud()

        data = None

        if os.path.exists(encodings_path):
            logger.info('Открытие файла кодировок...')
            try:
                with open(encodings_path, "rb") as file:
                    data = pickle.load(file)
            except Exception as ex:
                logger.exception(f'При попытке открытия файла {encodings_path} возникло исключение: {ex}')

        if employees:
            ids = employees['ids']
            if data:
                logger.info('Поиск изменений...')
                changes = list(set(data['ids']) ^ set(ids))
                logger.info(f'Найдено {len(changes)} изменений')
            else:
                data = {"ids": [], "photos": [], "encodings": [], "names": []}
                changes = ids

            if len(changes) > 0:
                logger.info('Создание кодировок...')

            delete = []
            new_counter = 0
            created_counter = 0
            if changes:
                for emp_id in tqdm(changes, colour='green'):
                    if emp_id not in ids:
                        delete.append(emp_id)
                        continue
                    new_counter += 1
                    i = ids.index(emp_id)
                    name = employees['names'][i]
                    cv_image = bytes_to_cv(employees['photos'][i])
                    encodings = self.app.get(cv_image)
                    for encoding in encodings:
                        try:
                            data["ids"].append(emp_id)
                            data["photos"].append(cv2.resize(cv_image, (0, 0), fx=0.3, fy=0.3))
                            data["encodings"].append(encoding.embedding)
                            data["names"].append(name)
                            created_counter += 1
                        except Exception as ex:
                            logger.exception(ex)
                logger.info(f'Создано кодировок: {created_counter} из {new_counter}')

            if delete:
                logger.info('Удаление старых кодировок...')
                for emp_id in delete:
                    i = data["ids"].index(emp_id)
                    for key in data.keys():
                        data[key].pop(i)
                logger.info(f'Удалено кодировок: {len(delete)}')

            if len(changes) > 0:
                logger.info('Сохранение файла с кодировками...')
                with open(encodings_path, "wb") as file:
                    pickle.dump(data, file)
        elif not data:
            logger.warning('Файл с кодировками не создан!')
        return data

    def save_photo(self, frame, name, photo):
        if self.record:
            frame = add_source_photo(frame, photo)
            create(Detection, name=name, photo=cv_image_to_bytes(frame))
            logger.debug(f"Сохранена запись для {name} в БД")

    @classmethod
    def recognize(cls, face: Face, encodings: Dict, distance: float) -> Optional[Tuple[str, np.ndarray]]:
        for i, encoding in enumerate(encodings['encodings']):
            result_distance = spatial.distance.cosine(face.embedding, encoding)
            if result_distance < distance:
                name = encodings['names'][i]
                photo = encodings['photos'][i]
                return name, photo
        return None

    def start(self, intervals, unknown_save_step=10, width=1024, skipped_frames_coeff=50, faces_distance=0.55):
        logger.info('Запуск...')
        video_capture = self.video_capture
        logger.info('В работе!')
        skipped_frames = 0  # количество пропускаемых кадров для синхронизации времени
        unknown_encodings = {"photos": [], "encodings": [], "names": []}
        while True:

            ret, frame = video_capture.read()

            if not ret:
                logger.debug("Отсутствует подключение к видеопотоку! Восстановление подключения...")
                video_capture = cv2.VideoCapture(self.video_source)
                logger.info('В работе!')
                continue

            full_frame = np.copy(frame)

            for interval in intervals:
                print(intervals, self.video_source)
                now = datetime.datetime.now().strftime("%H:%M")
                if interval[0] <= now <= interval[1]:
                    self.stop = False
                else:
                    self.stop = True

            if not self.stop:
                y1, y2, x1, x2 = self.crop
                frame = frame[y1:y2, x1:x2]

                if skipped_frames == 0:
                    start_detection = time.time()
                    faces = self.app.get(frame)
                    faces_found = True if faces else False
                    boxes = []
                    names = []
                    for face in faces:
                        name_counter_step = 1
                        box = face.bbox.astype(np.int64)

                        known = self.recognize(face, self.encodings, faces_distance)
                        if known:
                            name, photo = known
                            name_counter_step = unknown_save_step
                            color = (0, 255, 0)
                        else:
                            unknown = self.recognize(face, unknown_encodings, faces_distance - 0.20)
                            if unknown:
                                name, photo = unknown
                                color = (255, 0, 0)
                            else:
                                name = str(time.time())
                                x1, y1, x2, y2 = box
                                photo = frame[y1 - 20:y2 + 20, x1 - 20:x2 + 20]
                                color = (0, 0, 255)
                                unknown_encodings['encodings'].append(face.embedding)
                                unknown_encodings['names'].append(name)
                                unknown_encodings['photos'].append(photo)

                        count = self.detected_faces.get(name, 0)
                        count += name_counter_step
                        self.detected_faces[name] = count

                        if count % unknown_save_step == 0:
                            self.save_photo(
                                add_name(frame, name, box, color),
                                name,
                                photo
                            )

                        logger.info(f'Обнаружен(а): {name}')

                        boxes.append((box, color))
                        names.append(name)

                    detection_time = time.time() - start_detection
                    if faces_found:
                        skipped_frames = ceil(detection_time * skipped_frames_coeff)
                else:
                    skipped_frames -= 1

                # отображаем рамки лиц, пока пропускаются кадры
                if faces_found:
                    for box, name in zip(boxes, names):
                        box, color = box
                        frame = add_name(frame, name, box, color)

                y1, y2, x1, x2 = self.crop
                full_frame[y1:y2, x1:x2] = frame
                cv2.rectangle(full_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

            # масштабируем окно
            frame_height, frame_width, _ = full_frame.shape
            ratio = width / frame_width
            full_frame = cv2.resize(full_frame, (int(width), int(frame_height * ratio)))

            frame = add_logo(add_datetime(full_frame))
            ret, frame = cv2.imencode('.jpg', frame)
            frame = frame.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
