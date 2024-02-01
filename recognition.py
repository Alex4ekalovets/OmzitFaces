import face_recognition
import cv2
import numpy as np
from itertools import cycle

from utils.common import img_path
from utils.cv import add_logo

video_capture = cv2.VideoCapture(0)

my_image = face_recognition.load_image_file(img_path('chekalovetsav'))
my_face_encoding = face_recognition.face_encodings(my_image)[0]

known_face_encodings = [
    my_face_encoding,
]
known_face_names = [
    "Чекаловец А.В.",
]

face_locations = []
face_encodings = []
face_names = []
frequency = range(10)  # Частота обработки (каждый N кадр)
process_this_frame = cycle(frequency)
detected_faces = dict()

while True:
    ret, frame = video_capture.read()

    if not ret:
        break

    if next(process_this_frame) == 0:
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Преобразование цвета BGR (OpenCV) в цвет RGB (face_recognition)
        rgb_small_frame = np.ascontiguousarray(frame[:, :, ::-1])

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Не опознано"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]

            face_names.append(name)
            for face_name in face_names:
                count = detected_faces.get(face_name, 0)
                count += 1
                detected_faces[face_name] = count

    # Добавляем в угол текст с именами и количеством зафиксированных распознаваний
    text = ', '.join([f'{face}: {count}' for face, count in detected_faces.items()])
    cv2.putText(
        img=frame,
        text=text,
        org=(30, 30),
        fontScale=0.5,
        color=(0, 0, 255),
        thickness=1,
        fontFace=cv2.FONT_HERSHEY_COMPLEX,
    )
    cv2.imshow('OmZIT Faces', add_logo(frame))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print(detected_faces)
        break

video_capture.release()
cv2.destroyAllWindows()
