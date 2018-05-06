import os

ALLOW_IMAGE = (
    '.jpg',
    '.JPG',
    '.jpeg',
    '.png',
)


def listdir(path='../faceset'):
    list_name = {}
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.splitext(file_path)[1] in ALLOW_IMAGE:
            name = file.split('.')[0]
            list_name.update({name: file_path})
    return list_name
