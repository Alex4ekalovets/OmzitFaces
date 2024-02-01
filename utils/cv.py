import cv2
import numpy as np


def face_detected(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_classifier = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    face = face_classifier.detectMultiScale(
        gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
    )
    is_detected = isinstance(face, np.ndarray)
    return is_detected


def add_logo(frame):
    frame_height, _ = frame.shape

    logo = cv2.imread('static/img/logo.png', cv2.IMREAD_UNCHANGED)
    img_height, _ = logo.shape

    ratio = img_height / frame_height

    logo = cv2.resize(logo, (0, 0), fx=ratio, fy=ratio)

    img_height, img_width, _ = logo.shape

    x = 20
    y = int(frame_height - img_height - 10)

    new_frame = np.copy(frame)
    place = new_frame[y: y + logo.shape[0], x: x + logo.shape[1]]
    a = logo[..., 3:].repeat(3, axis=2).astype('uint16')
    place[...] = (place.astype('uint16') * (255 - a) // 255) + logo[..., :3].astype('uint16') * a // 255
    return new_frame

