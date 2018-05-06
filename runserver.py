import sys
from facerec_from_webcam import Video, FaceSet

operations = (
    'init',
    'show'
)

if __name__ == '__main__':
    args = sys.argv
    action = args[1]
    outer_id = args[2]
    # outer_id = 'downtown1'
    if action == 'init':

        # 获取每个照片的face_token
        face_dict = FaceSet.load_faceset(path='./faceset')

        # 创建faceset
        FaceSet.create_faceset(outer_id=outer_id)

        # face_token存入faceset中
        FaceSet.add_face(outer_id=outer_id, face_tokens=[k for k, v in face_dict.items()])

    elif action == 'show':
        ip = 'rtsp://192.168.124.2:554/1/h264major'
        video = Video(ip_address=0)
        # video.connect()
        video.show2(outer_id=outer_id)
    print('哟哟stop it now')
