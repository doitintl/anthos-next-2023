from tempfile import NamedTemporaryFile, TemporaryFile
# import cv2
from flask import Flask
import datetime
import os
from minio import Minio
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {
        'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    },
    'console': {
        "class": "logging.StreamHandler",
        "stream": "ext://sys.stdout",
        "formatter": "default",
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
})

app = Flask(__name__)

client = Minio(
    os.environ["MINIO_HOST"],
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"],
    secure=False,
)


def capture_image():
    try:

        filename = f"{datetime.datetime.utcnow().isoformat()}.jpg"
        app.logger.info(f"filename is {filename}")
        with NamedTemporaryFile(suffix=".jpg") as temp:

            app.logger.info(f"capturing image to tempfile {temp.name}")
            output = os.system(f"v4l2-ctl --device /dev/video0 --set-fmt-video=width=640,height=480,pixelformat=MJPG --stream-mmap --stream-to={temp.name} --stream-count=1")
            app.logger.info(f"v4l2-ctl output: {output}")
            app.logger.info(f"putting image to bucket {filename}")
            client.fput_object(
                "images", filename, temp.name,
            )

        return True
    except Exception as e:
        app.logger.info(f"failed to capture image: {e}")
        return False





@app.route("/capture")
def capture():
    stat = capture_image()
    return "captured" if stat else "failed"


@app.route("/notify")
def notify():
    app.logger.info("image create notified")
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)