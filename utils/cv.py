import datetime
import io

import cv2
import numpy as np
from Cython.Shadow import _ArrayType
from PIL import Image


def cv_image_to_bytes(image: _ArrayType) -> bytes:
    photo = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    photo = Image.fromarray(photo)
    buffer = io.BytesIO()
    photo.save(buffer, format='png')
    byte_photo = buffer.getvalue()
    return byte_photo


def bytes_to_cv(bytes_image):
    pil_image = Image.open(io.BytesIO(bytes_image))
    pil_image = pil_image.convert('RGB')
    open_cv_image = np.array(pil_image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()
    return open_cv_image


def get_sharpness(frame, face_location):
    for i in range(4):
        if face_location[i] < 0:
            face_location[i] = 0
    face_img = frame[face_location[1]:face_location[3], face_location[0]:face_location[2]]
    sharpness = int(cv2.Laplacian(face_img, cv2.CV_64F).var())
    return sharpness


def add_logo(frame):
    frame_height, _, _ = frame.shape
    logo = cv2.imread('static/img/logo.png', cv2.IMREAD_UNCHANGED)
    img_height, _, _ = logo.shape
    logo = cv2.resize(logo, (0, 0), fx=0.5, fy=0.5)
    img_height, img_width, _ = logo.shape
    x = 20
    y = int(frame_height - img_height - 10)
    new_frame = np.copy(frame)
    place = new_frame[y: y + logo.shape[0], x: x + logo.shape[1]]
    a = logo[..., 3:].repeat(3, axis=2).astype('uint16')
    place[...] = (place.astype('uint16') * (255 - a) // 255) + logo[..., :3].astype('uint16') * a // 255
    return new_frame


def add_source_photo(frame, photo):
    try:
        frame_height, _, _ = frame.shape

        min_photo = photo
        img_height, img_width, _ = min_photo.shape

        y = 150
        x = int(img_width * y / img_height)

        min_photo = cv2.resize(min_photo, (x, y))

        img_height, img_width, _ = min_photo.shape

        x = 20
        y = int(frame_height - img_height - 10)
        new_frame = np.copy(frame)
        new_frame[y: y + img_height, x: x + img_width] = min_photo
        return new_frame
    except:
        pass


def add_name(frame, name, face_location, color=None):
    if len(face_location) > 4:
        y1, x2, y2, x1 = face_location[:5]
    else:
        x1, y1, x2, y2 = face_location

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
    font = cv2.FONT_HERSHEY_COMPLEX
    parts = name.split()
    scale = ((x2 - x1) / 11.5) / max(map(len, parts))
    offset = 5
    cv2.rectangle(frame, (x1, y1), (x2, int(y1 - offset - 15 * len(parts) * scale)), color, -1)
    for name_part in parts[::-1]:
        cv2.putText(frame, name_part, (x1, y1 - offset), font, 0.5 * scale, (0, 0, 0), 1)
        offset += int(15 * scale)
    return frame


def add_datetime(frame):
    font = cv2.FONT_HERSHEY_TRIPLEX
    text_color = (255, 255, 255)
    offset = 10
    scale = 0.5
    text = datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    cv2.putText(frame, text, (0 + offset, 5 + offset), font, scale, text_color, 1)
    return frame
