import json
from tempfile import NamedTemporaryFile

from flask import Flask, request, render_template, Response
import datetime
import os
from minio import Minio
from logging.config import dictConfig
# pubsub libraries
from google.cloud import pubsub_v1

# OCR libraries
from PIL import Image
import pytesseract


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

minio_client = Minio(
    os.environ["MINIO_HOST"],
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"],
    secure=False,
)

if os.environ["IS_CAPTURING"] == "true":
    @app.route("/capture")
    def capture():
        stat, image_name = capture_image()
        return json.dumps({"message": "OK", "image_name": image_name}) if stat else json.dumps({"message": "error"}), 500

    @app.route("/")
    def index():
        return render_template("index.html", **{})
    
    @app.route("/clear")
    def clear():
        # delete the file static/image.jpg
        os.remove("static/image.jpg")

    def capture_image():
        try:

            filename = f"{datetime.datetime.utcnow().isoformat()}.jpg"
            app.logger.info(f"filename is {filename}")
            with NamedTemporaryFile(suffix=".jpg") as temp:

                app.logger.info(f"capturing image to tempfile {temp.name}")
                output = os.system(f"v4l2-ctl --device /dev/video0 --set-fmt-video=width=640,height=480,pixelformat=MJPG --stream-mmap --stream-to={temp.name} --stream-count=1")
                app.logger.info(f"v4l2-ctl output: {output}")
                app.logger.info(f"putting image to bucket {filename}")
                minio_client.fput_object(
                    "images", filename, temp.name,
                )

                # always overwrite image.jpg with the latest image
                with open("static/image.jpg", "wb") as f:
                    f.write(temp.read())

            return True, filename
        except Exception as e:
            app.logger.info(f"failed to capture image: {e}")
            return False, None
else:



    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path("davec-anthos-next", "data")

    @app.route("/notify", methods=['POST'])
    def notify():
        app.logger.info("image create notified")
        app.logger.info(f"request json {request.json}")

        image_name = request.json["Key"]

        with NamedTemporaryFile(suffix=".jpg") as temp:
            (bucket, filename) = image_name.split("/")
            app.logger.info(f"downloading image {bucket}/{filename} to tempfile {temp.name}")
            minio_client.fget_object(bucket, filename, temp.name)
            app.logger.info(f"image downloaded to tempfile {temp.name}")
            msg = pytesseract.image_to_string(Image.open(temp.name))
            app.logger.info(f"image text: {msg}")
        
        msg = "no text found" if msg == "" else msg

        publish_future = publisher.publish(topic_path, msg.encode("utf-8"))
        app.logger.info(f"publish result: {publish_future.result()}")
        return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)