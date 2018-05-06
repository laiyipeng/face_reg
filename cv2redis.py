from facerec_from_webcam import Video

if __name__ == '__main__':
    ip = 'rtsp://192.168.124.2:554/1/h264major'
    video = Video(ip_address=0)
    video.connect()
    video.cv2cache()
