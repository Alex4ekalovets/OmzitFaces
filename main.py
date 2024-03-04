import logging

from multiprocessing import Queue

from settings import SOURCES
from recognition import InsightFace

logger = logging.getLogger("logger")


def start_in_process(n, manager: Queue, crop):
    rec = InsightFace(**SOURCES[n]['create'])

    for i in range(4):
        crop[i] = int(rec.crop[i])

    frame_gen = rec.start(**SOURCES[n]['start'])
    rec.stop = not SOURCES[n]['stream']['is_recognized']
    rec.record = SOURCES[n]['stream']['is_record']

    while True:
        try:
            result = next(frame_gen)
            manager.put(result)
            if manager.qsize() > 3:
                manager.get()
        except StopIteration:
            return


if __name__ == "__main__":
    pass
