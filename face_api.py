import requests
import json


class FaceApi(object):
    app_name = 'faceID'
    host = 'https://api-cn.faceplusplus.com'
    uri_body_detect = '/humanbodypp/v1/detect'
    uri_face_detect = '/facepp/v3/detect'
    uri_face_compare = '/facepp/v3/compare'
    uri_faceset_create = '/facepp/v3/faceset/create'
    uri_faceset_face_add = '/facepp/v3/faceset/addface'
    uri_faceset_face_remove = '/facepp/v3/faceset/removeface'
    uri_faceset_search = '/facepp/v3/search'

    def __init__(self, api_key, secret_key, face_dict_path):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_body = {
            'api_key': self.api_key,
            'api_secret': self.secret_key
        }
        with open(face_dict_path, 'rb') as f:
            face_dict = f.read()
        self.face_dict = json.loads(face_dict)

    def body_recognized(self, image):
        """
        体态识别
        :param image:
        :return:
        """
        body = self.base_body.copy()
        body.update(return_attributes='gender')
        files = {'image_file': image}
        resp = requests.post(self.host + self.uri_body_detect, data=body, files=files).json()
        res = [(human['humanbody_rectangle']['top'],
                human['humanbody_rectangle']['left'] + human['humanbody_rectangle']['width'],
                human['humanbody_rectangle']['top'] + human['humanbody_rectangle']['height'],
                human['humanbody_rectangle']['left'],
                'male' if human['attributes']['gender']['male'] > 50 else 'female')
               for human in resp.get('humanbodies', [])]
        return res

    def get_face_token(self, image_path):
        """
        获取图片中人物的face_token
        :param image_path: 图片路径
        :return: face_token
        """
        body = self.base_body.copy()
        with open(image_path, 'rb') as f:
            image = f.read()
        files = {'image_file': image}
        resp = requests.post(self.host + self.uri_face_detect, data=body, files=files).json()
        res = resp.get('faces')[0]['face_token']
        return res

    def face_recognized(self, image, outer_id='', show_name=True):
        """
        面部识别
        :param image:
        :param outer_id:
        :param show_name:
        :return:
        """
        body = self.base_body.copy()
        body.update({'return_attributes': 'gender,age,emotion,ethnicity,beauty'})
        files = {'image_file': image}
        resp = requests.post(self.host + self.uri_face_detect, data=body, files=files).json()
        res = []
        if show_name:
            for face in resp.get('faces', []):
                face_token = face['face_token']
                face_name = self.face_search(face_token, outer_id)
                res.append((face['face_rectangle']['top'],
                           face['face_rectangle']['left'] + face['face_rectangle']['width'],
                           face['face_rectangle']['top'] + face['face_rectangle']['height'],
                           face['face_rectangle']['left'],
                           '{},{},{},{},{}'.format(face_name,
                                                   face['attributes']['gender']['value'],
                                                   face['attributes']['age']['value'],
                                                   sorted(resp['faces'][0]['attributes']['emotion'].items(),
                                                          key=lambda x: x[1])[-1][0],
                                                   face['attributes']['ethnicity']['value'])))
        else:
            res = [(face['face_rectangle']['top'],
                    face['face_rectangle']['left'] + face['face_rectangle']['width'],
                    face['face_rectangle']['top'] + face['face_rectangle']['height'],
                    face['face_rectangle']['left'],
                    '{},{},{},{}'.format(face['attributes']['gender']['value'],
                                         face['attributes']['age']['value'],
                                         sorted(resp['faces'][0]['attributes']['emotion'].items(), key=lambda x: x[1])[
                                             -1][0],
                                         face['attributes']['ethnicity']['value']))
                   for face in resp.get('faces', [])]
        return res

    def face_compare(self, image, image_path='lai.jpg'):
        """
        两张图片对比
        :param image:
        :param image_path:
        :return:
        """
        body = self.base_body.copy()
        with open(image_path, 'rb') as f:
            image_set = f.read()
        files = {'image_file1': image, 'image_file2': image_set}
        resp = requests.post(self.host + self.uri_face_compare, data=body, files=files).json()
        res = [(face['face_rectangle']['top'],
                face['face_rectangle']['left'] + face['face_rectangle']['width'],
                face['face_rectangle']['top'] + face['face_rectangle']['height'],
                face['face_rectangle']['left'],
                'lai' if resp.get('confidence', 0) >= 60 else 'unknown')
               for face in resp.get('faces1', [])]
        return res

    def faceset_create(self, display_name='downtown', outer_id='downtown1', tags='', face_tokens='', user_data='',
                       force_merge=''):
        """
        创建faceset集合
        :param display_name: 人脸集合的名字，最长256个字符，不能包括字符^@,&=*'"
        :param outer_id: 账号下全局唯一的 FaceSet 自定义标识，可以用来管理 FaceSet 对象。最长255个字符，不能包括字符^@,&=*'"
        :param tags: FaceSet 自定义标签组成的字符串，用来对 FaceSet 分组。最长255个字符，多个 tag 用逗号分隔，每个 tag 不能包括字符^@,&=*'"
        :param face_tokens: 人脸标识 face_token，可以是一个或者多个，用逗号分隔。最多不超过5个 face_token
        :param user_data: 自定义用户信息，不大于16 KB，不能包括字符^@,&=*'"
        :param force_merge: 在传入 outer_id 的情况下，如果 outer_id 已经存在，是否将 face_token 加入已经存在的 FaceSet 中
                0：不将 face_tokens 加入已存在的 FaceSet 中，直接返回 FACESET_EXIST 错误
                1：将 face_tokens 加入已存在的 FaceSet 中
                默认值为0
        :return:
        """
        body = self.base_body.copy()
        body.update(display_name=display_name, outer_id=outer_id)
        resp = requests.post(self.host + self.uri_faceset_create, data=body).json()
        # try:
        #     red.set('faceset_token_'.format(outer_id), resp['faceset_token'])
        # except Exception as e:
        #     print(e)
        return resp

    def faceset_add_face(self, outer_id, face_tokens):
        """
        faceset添加face_token
        :param outer_id: 用户提供的 FaceSet 标识
        :param face_tokens: 人脸标识 face_token 组成的字符串，可以是一个或者多个，用逗号分隔。最多不超过5个face_token
        :return:
        """
        body = self.base_body.copy()
        body.update(outer_id=outer_id, face_tokens=face_tokens)
        resp = requests.post(self.host + self.uri_faceset_face_add, data=body).json()
        return resp

    def faceset_remove_face(self, outer_id, face_tokens):
        """
        faceset移除face_token
        :param outer_id: 用户提供的 FaceSet 标识
        :param face_tokens: 人脸标识 face_token 组成的字符串，可以是一个或者多个，用逗号分隔。最多不超过5个face_token
        :return:
        """
        body = self.base_body.copy()
        body.update(outer_id=outer_id, face_tokens=face_tokens)
        resp = requests.post(self.host + self.uri_faceset_face_remove, data=body).json()
        return resp

    def face_search(self, face_token, outer_id):
        """
        faceset查找face_token
        :param face_token:
        :param outer_id:
        :return:
        """
        while True:
            body = self.base_body.copy()
            body.update(outer_id=outer_id, face_token=face_token)
            resp = requests.post(self.host + self.uri_faceset_search, data=body).json()
            if resp.get('error_message'):
                continue
            result = resp.get('results', [])
            if result:
                name = self.face_dict.get(result[0]['face_token'], 'unknown') \
                    if result[0]['confidence'] >= 70 else 'unknown'
            else:
                name = 'unknown'
            break
        return name


face_api = FaceApi(api_key='60VvXGtIpK50VBe4kMFKSteisSpnwKib',
                   secret_key='xzqzszLkqlM9_Jvo8TsFWa49clnKWEkI',
                   face_dict_path='./faceset/face_dict.json')
