import datetime
from threading import Thread

from PIL import Image
from imutils import paths
import face_recognition
import imutils
import pickle
import cv2
import os


# в директории Images хранятся папки со всеми изображениями
def foo():
    imagePaths = list(paths.list_images('Images'))
    knownEncodings = []
    knownNames = []
    for (i, imagePath) in enumerate(imagePaths):
        name = imagePath.split(os.path.sep)[-2]
        image = cv2.imread(imagePath)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model='hog')
        encodings = face_recognition.face_encodings(rgb, boxes)
        for encoding in encodings:
            knownEncodings.append(encoding)
            knownNames.append(name)
    data = {"encodings": knownEncodings, "names": knownNames}
    f = open("face_enc", "wb")
    f.write(pickle.dumps(data))
    f.close()


class OCR:

    def __init__(self):
        self.exchange = None
        self.stopped = False
        self.cascPathface = os.path.dirname(
            cv2.__file__) + "/data/haarcascade_frontalface_alt2.xml"
        self.faceCascade = cv2.CascadeClassifier(self.cascPathface)
        self.new_frame = None
        self.recognized_people = set()

    def start(self):
        Thread(target=self.ocr, args=()).start()
        return self

    def set_exchange(self, video_stream):
        self.exchange = video_stream

    def ocr(self):
        try:
            while not self.stopped:
                self.data = pickle.loads(open('face_enc', "rb").read())
                if self.exchange is not None:
                    frame = self.exchange.frame
                    if self.exchange.ret:
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        encodings = face_recognition.face_encodings(rgb, model="large")
                        names = []
                        for encoding in encodings:
                            matches = face_recognition.compare_faces(self.data["encodings"],
                                                                     encoding)
                            name = "Unknown"
                            if True in matches:
                                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                                counts = {}
                                for i in matchedIdxs:
                                    name = self.data["names"][i]
                                    counts[name] = counts.get(name, 0) + 1
                                name = max(counts, key=counts.get)

                            names.append(name)
                            current_time = datetime.datetime.now()

                            face_locations = face_recognition.face_locations(rgb, model='hog')
                            for face_location in face_locations:
                                if face_location not in ((1258, 2286, 1332, 2211),):
                                    if name == "Unknown":
                                        folder_name = f"{current_time.strftime('%Y.%m.%d %H-%M-%S-%f')}"
                                        if not os.path.exists(fr"D:\Projects\pythonProject\FaceDetector\Images\{folder_name}"):
                                            os.mkdir(fr"D:\Projects\pythonProject\FaceDetector\Images\{folder_name}")

                                        top, right, bottom, left = face_location

                                        print(face_location)

                                        face_img = rgb[top - 20:bottom + 20, left - 20:right + 20]
                                        img = Image.fromarray(face_img)
                                        img.save(
                                            fr"D:\Projects\pythonProject\FaceDetector\Images\{folder_name}\{int(round(current_time.timestamp()))}.jpg")
                                    elif name == "ChekalovetsAV":
                                        top, right, bottom, left = face_location

                                        print(face_location)

                                        face_img = rgb[top - 20:bottom + 20, left - 20:right + 20]
                                        img = Image.fromarray(face_img)
                                        img.save(
                                            fr"D:\Projects\pythonProject\FaceDetector\Images\{name}\{int(round(current_time.timestamp()))}.jpg")

                            if name == "Unknown":
                                foo()

                            self.recognized_people.add(name)
                            print(current_time, name)

                        if len(encodings) != 0:
                            self.new_frame = frame
                        else:
                            self.new_frame = None
        except Exception as ex:
            print(ocr, ex)
    def stop_process(self):
        self.stopped = True


class VideoStream:
    """
    Class for CV2 video capture. The start() method will create a new
    thread to read the video stream
    """

    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.ret, self.frame = self.stream.read()
        self.stopped = False
        self.count = 1

    def start(self):
        Thread(target=self.get, args=()).start()
        return self

    def get(self):
        while not self.stopped:
            self.ret, self.frame = self.stream.read()
            if not self.ret:
                self.stop_process()

    def take_screenshot(self):
        print(f'Screenshot {self.count}')
        cv2.imwrite(fr"D:\Projects\pythonProject\FaceDetector\Images\ChekalovetsAV\{self.count}.jpg", self.frame)
        self.count += 1

    def get_video_dimensions(self):
        width = self.stream.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT)
        return int(width), int(height)

    def stop_process(self):
        self.stopped = True


def stop_stream_ocr(stream, ocr):
    stream.stop_process()
    ocr.stop_process()


if __name__ == "__main__":
    foo()
    exchange = VideoStream(r'D:\Projects\pythonProject\FaceDetector\01_20231218_114201.avi').start()  # "rtsp://admin01:Epass1@192.168.9.15:554"  D:\Projects\pythonProject\FaceDetector\01_20231215_103650.avi
    ocr = OCR().start()
    ocr.set_exchange(exchange)

    try:
        while True:
            pressed_key = cv2.waitKey(1) & 0xFF
            if pressed_key == ord('q'):
                stop_stream_ocr(exchange, ocr)
                break
            elif pressed_key == ord('s'):
                exchange.take_screenshot()
            elif pressed_key == ord('r'):
                print(f'Распознанные люди: {", ".join(ocr.recognized_people)}')

            frame = exchange.frame

            # if ocr.new_frame is None:
            #     frame = exchange.frame
            # else:
            #     frame = ocr.new_frame

            frame = imutils.resize(frame, width=640)
            cv2.imshow("Video Get Frame", frame)
    except Exception as ex:
        print(ex)