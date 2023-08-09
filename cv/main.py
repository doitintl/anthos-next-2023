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
    try:

        filename = f".{datetime.datetime.utcnow().isoformat()}.jpg"
        print(f"filename is {filename}")
        with NamedTemporaryFile(suffix=".jpg") as temp:

            print(f"capturing image to tempfile {temp.name}")
            output = os.system(f"v4l2-ctl --device /dev/video0 --set-fmt-video=width=100,height=100,pixelformat=MJPG --stream-mmap --stream-to={temp.name} --stream-count=1")
            print(f"v4l2-ctl output: {output}")
            print(f"putting image to bucket {filename}")
            client.fput_object(
                "images", filename, temp.name,
            )

        return True
    except Exception as e:
        print(f"failed to capture image: {e}")
        return False


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