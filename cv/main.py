from tempfile import NamedTemporaryFile, TemporaryFile
# import cv2
from flask import Flask
import datetime
import os
from minio import Minio

client = Minio(
    os.environ["MINIO_HOST"],
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"],
)


def capture_image():
    # capture = cv2.VideoCapture(0)

    # if not capture.isOpened():
    #     print("no camera found")
    #     capture.release()
    #     return False

    # ret, frame = capture.read()

    filename = f".{datetime.datetime.utcnow().isoformat()}.jpg"
    with NamedTemporaryFile(suffix=".jpg") as temp:
        # capture a picture with v4l2
        print(f"capturing image to tempfile {temp.name}")

        output = os.system(f"v4l2-ctl --device /dev/video0 --set-fmt-video=width=100,height=100,pixelformat=MJPG --stream-mmap --stream-to={temp.name} --stream-count=1")
        print(f"v4l2-ctl output: {output}")


        # cv2.imwrite(temp.name, frame)
        print(f"putting image to bucket {filename}")
        client.fput_object(
            "images", filename, temp.name,
        )
    capture.release()
    return True


# write a small flask REST api to capture image

app = Flask(__name__)


@app.route("/capture")
def capture():
    stat = capture_image()
    return "captured" if stat else "failed"


@app.route("/notify")
def notify():
    print("image create notified")
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)