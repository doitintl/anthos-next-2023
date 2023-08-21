import io
import json
from tempfile import NamedTemporaryFile
from prometheus_flask_exporter import PrometheusMetrics

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
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version=os.environ["APP_VERSION"])


minio_client = Minio(
    os.environ["MINIO_HOST"],
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"],
    secure=False,
)

if os.environ["IS_CAPTURING"] == "true":
    @app.route("/capture")
    def capture():
        try:

            filename = f"{datetime.datetime.utcnow().isoformat()}.jpg"
            app.logger.info(f"filename is {filename}")
            with NamedTemporaryFile(suffix=".jpg") as temp:

                app.logger.info(f"capturing image to tempfile {temp.name}")
                output = os.system(f"v4l2-ctl --device /dev/video0 --silent --set-fmt-video=width=640,height=480,pixelformat=MJPG --stream-mmap --stream-to={temp.name} --stream-count=1")
                app.logger.info(f"v4l2-ctl output: {output}")
                if int(output) != 0:
                    app.logger.info(f"v4l2-ctl failed with exit code {output}")
                    return {"message": "error", "error": e}, 500
                app.logger.info(f"putting image to bucket {filename}")
                minio_client.fput_object("images", filename, temp.name)

                app.logger.info(f"writing image to static/image.jpg")
                # always overwrite image.jpg with the latest image
                with open("static/image.jpg", "wb") as f:
                    f.write(temp.read())

            return {"message": "OK", "image_name": filename}, 200
        except Exception as e:
            app.logger.info(f"failed to capture image: {e}")
            return {"message": "error", "error": e}, 500
        

    @app.route("/")
    def index():
        return render_template("index.html", **{})
    
    @app.route("/clear")
    def clear():
        # delete the file static/image.jpg
        os.remove("static/image.jpg")
        return {"message": "OK"}, 200 
        

    @app.route("/messages")
    def messages():
        subscriber = pubsub_v1.SubscriberClient()
        subscription_path = subscriber.subscription_path("davec-anthos-next", "data-sub")
        with subscriber:
            response = subscriber.pull(request={"subscription": subscription_path, "max_messages": 10})

            ack_ids = []
            messages = []
            for received_message in response.received_messages:
                app.logger.info(f"Received: {received_message.message.data}.")
                ack_ids.append(received_message.ack_id)
                messages.append(received_message.message.data.decode("utf-8"))

            # Acknowledges the received messages so they will not be sent again.
            subscriber.acknowledge(
                request={"subscription": subscription_path, "ack_ids": ack_ids}
            )

            return {"message": "OK", "messages": messages}, 200
            
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
        
        with io.BytesIO(bytes(msg, 'utf-8')) as msg_stream:
            minio_client.put_object("cv-output", filename, msg_stream, -1, part_size=1024*1024*10)

        # publish_future = publisher.publish(topic_path, msg.encode("utf-8"))
        # app.logger.info(f"publish result: {publish_future.result()}")
        return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)