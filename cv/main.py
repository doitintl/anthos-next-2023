import cv2
import sys

if __name__ == "__main__":
    print( "Hello World!")
    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        sys.exit(1)

    ret, frame = capture.read()

    cv2.imwrite('{}_{}.{}'.format("/images/test.jpg"), frame)

