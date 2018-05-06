import cv2
import base64
import time
import numpy as np
import json
from PIL import Image, ImageDraw, ImageFont

from face_api import face_api
from util.common import listdir
from db_base import red


class Video(object):
    video_capture = None
    rec_image_list = []
    rec_face_encoding_list = []

    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.red = red

    def connect(self):
        video_capture = cv2.VideoCapture(self.ip_address)
        self.video_capture = video_capture
        return video_capture

    def disconnect(self):
        self.video_capture.release()
        self.video_capture = None
        cv2.destroyAllWindows()

    def cv2cache(self):
        while True:
            ret, frame = self.video_capture.read()
            if ret:
                # rgb_frame = frame[:, :, ::-1]
                rgb_frame = frame
                rgb_frame = cv2.resize(rgb_frame, (720, 480), interpolation=cv2.INTER_CUBIC)
                np.save("filename.npy", rgb_frame)
                rgb_frame = cv2.resize(rgb_frame, (1440, 960), interpolation=cv2.INTER_CUBIC)
                cv2.imshow('Video', rgb_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                # 断出重连
                print('connect again')
                self.connect()

    @staticmethod
    def frame2base64(frame):
        # array转换base64
        ret, buffer = cv2.imencode('.png', frame)
        jpg_as_text = base64.b64encode(buffer)
        jpg_as_text = base64.decodestring(jpg_as_text)
        return jpg_as_text

    def _load_faces(self, image_list):
        self.rec_image_list = ['lai', 'obama']
        rec_face_encoding_list = []

        # 载入图片
        for name in self.rec_image_list:
            rec_image = face_recognition.load_image_file("{}.jpg".format(name))
            rec_face_encoding_list.append(face_recognition.face_encodings(rec_image)[0])
        self.rec_face_encoding_list = rec_face_encoding_list

    def face_encode(self, frame):
        # 找到人脸位置并且encoding
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # 对比人脸
            match = face_recognition.compare_faces(self.rec_face_encoding_list, face_encoding)

            name = "Unknown"
            for index, _name in enumerate(self.rec_image_list):
                if match[index]:
                    name = _name

            # 画出人脸框
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # 将名字写在框内
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)
        return frame

    @staticmethod
    def _put_text(img, text, position):
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        font = ImageFont.truetype('util/simhei.ttf', 20)
        # 输出内容
        draw = ImageDraw.Draw(img)
        draw.text(position, text, font=font, fill=(255, 255, 0))

        # 转换回OpenCV格式
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        return img

    def _face_locate(self, frame, locations):
        for top, right, bottom, left, other in locations:
            # 画出人脸框
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            # 将名字写在框内
            # cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            frame = self._put_text(frame, other, (left + 6, bottom - 36))
            # font = cv2.FONT_HERSHEY_DUPLEX
            # cv2.putText(frame, other, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
        return frame

    def face_compare(self):
        pass

    def show(self, outer_id=''):
        while True:
            # 读取摄像头
            ret, frame = self.video_capture.read()

            if ret:
                rgb_frame = frame[:, :, ::-1]
                rgb_frame = cv2.resize(rgb_frame, (720, 480), interpolation=cv2.INTER_CUBIC)
                image = self.frame2base64(frame=rgb_frame)
                t1 = time.time()
                location = face_api.face_recognized(image=image, outer_id=outer_id, show_name=True)
                t2 = time.time()
                print('time1 used: ', t2 - t1)
                if location:
                    rgb_frame = self._face_locate(rgb_frame, location)
                    cv2.imshow('Video', rgb_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                # 断出重连
                print('connect again')
                self.connect()

        # 断开连接
        self.disconnect()

    def show2(self, outer_id=''):
        while True:
            try:
                rgb_frame = np.load("filename.npy")
                if rgb_frame.any():
                    image = self.frame2base64(frame=rgb_frame)

                    t1 = time.time()
                    location = face_api.face_recognized(image=image, outer_id=outer_id, show_name=True)
                    t2 = time.time()
                    print('time1 used: ', t2 - t1)
                    if location:
                        rgb_frame = self._face_locate(rgb_frame, location)
                        cv2.imshow('Video', rgb_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            except Exception as e:
                print(e)
                continue


class FaceSet(object):

    @classmethod
    def load_faceset(cls, path):
        """
        加载本地图片集合
        :return:
        """
        face_dict = {}
        face_set = listdir(path=path)
        for name, item_path in face_set.items():
            while True:
                try:
                    face_token = face_api.get_face_token(item_path)
                    face_dict[face_token] = name
                    break
                except Exception as e:
                    print(e)

        with open(path + '/face_dict.json', 'w') as f:
            f.write(json.dumps(face_dict))
            f.close()
        return face_dict

    @classmethod
    def create_faceset(cls, display_name='downtown', outer_id='downtown_test'):
        """
        创建face集合
        :return:
        """
        while True:
            try:
                res = face_api.faceset_create(display_name=display_name, outer_id=outer_id)
                if res.get('error_message') == 'CONCURRENCY_LIMIT_EXCEEDED':
                    continue
                break
            except Exception as e:
                print(e)
        return res

    @classmethod
    def add_face(cls, outer_id, face_tokens):
        """
        faceset增加face
        :return:
        """
        for face_token in face_tokens:
            while True:
                try:
                    res = face_api.faceset_add_face(outer_id, face_token)
                    if res.get('error_message') == 'CONCURRENCY_LIMIT_EXCEEDED':
                        continue
                    break
                except Exception as e:
                    print(e)
        return True

    @classmethod
    def remove_face(cls, outer_id, face_tokens):
        """
        faceset移除face
        :return:
        """
        return face_api.faceset_remove_face(outer_id, face_tokens)


if __name__ == '__main__':
    ip = 'rtsp://192.168.124.2:554/1/h264major'
    video = Video(ip_address=0)
    video.show2(outer_id='')
