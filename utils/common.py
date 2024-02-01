import os


def list_full_paths(directory='data/video'):
    return [os.path.join(directory, file) for file in os.listdir(directory)]


def img_path(name):
    for ext in ['jpeg', 'jpg', 'png', 'gif']:
        path = os.path.join('data/faces', f'{name}.{ext}')
        if os.path.exists(path):
            break
    return path
