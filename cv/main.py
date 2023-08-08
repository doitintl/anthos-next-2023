from tempfile import TemporaryFile
import cv2
from flask import Flask
import datetime
import os
from minio import Minio

client = Minio(
    'http://localhost:9000/',
    access_key="D7GROicQiR4UGVl1CRVh",
    secret_key="SAYxL5bcEXu6k0LrrOGypwRw6Aqmmi3GgFJFurSu",
)


def capture_image():
    capture = cv2.VideoCapture(0)

    if not capture.isOpened():
        print("no camera found")
        return False

    ret, frame = capture.read()

    filename = f".{datetime.datetime.utcnow().isoformat()}.jpg"


    with TemporaryFile() as temp:
        print(f"capturing image to tempfile {temp.name}")
        cv2.imwrite(temp.name, frame)
        capture.release()
        print(f"putting image to bucket {filename}")
        client.fput_object(
            "images", filename, temp.name,
        )
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