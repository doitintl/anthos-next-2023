import io
import json
from tempfile import NamedTemporaryFile
from prometheus_flask_exporter import PrometheusMetrics
from middleware import logger

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
            logger.info('filename', filename=filename)
            with NamedTemporaryFile(suffix=".jpg") as temp:

                logger.info("capturing image to tempfile", tempfile=temp.name)
                output = os.system(f"v4l2-ctl --device /dev/video0 --silent --set-fmt-video=width=1920,height=1080,pixelformat=MJPG --stream-mmap --stream-to={temp.name} --stream-count=1")
                logger.info("v4l2-ctl output", output=output)
                if int(output) != 0:
                    logger.error("v4l2-ctl failed with exit code", output=output)
                    return {"message": "error", "error": output}, 500
                logger.info("putting image to bucket", filename=filename)
                minio_client.fput_object("images", filename, temp.name)

                logger.info("writing image to static/image.jpg")
                # always overwrite image.jpg with the latest image
                with open("static/image.jpg", "wb") as f:
                    f.write(temp.read())

            return {"message": "OK", "image_name": filename}, 200
        except Exception as e:
            logger.error("failed to capture image", error=e)
            return {"message": "error", "error": e}, 500
        

    @app.route("/")
    def index():
        return render_template("index.html", **{})
    
    @app.route("/clear")
    def clear():
        # delete the file static/image.jpg
        os.remove("static/image.jpg")
        return {"message": "OK"}, 200 
        

    @app.route("/messages/<filename>")
    def messages(filename):

        temp = NamedTemporaryFile(suffix=".txt")
        logger.info("downloading message file to tempfile", tempfile=temp.name, message_file=f"${filename}.txt")
        minio_client.fget_object("cv-output", f"{filename}.txt", temp.name)
        logger.info("text downloaded to tempfile", tempfile=temp.name)

        with open(temp.name) as read_file:
            rtn = {"message": "OK", "messages": read_file.read()}, 200

        temp.close()
        # os.unlink(temp.name)
        return rtn
else:


    @app.route("/notify", methods=['POST'])
    def notify():
        logger.info("image create notified")
        logger.info("request json", request_json=request.json)

        image_name = request.json["Key"]

        with NamedTemporaryFile(suffix=".jpg") as temp:
            (bucket, filename) = image_name.split("/")
            logger.info("downloading image to tempfile", image=f"{bucket}/{filename}", tempname=temp.name)
            minio_client.fget_object(bucket, filename, temp.name)
            logger.info("image downloaded to tempfile", tempfile=temp.name)
            msg = pytesseract.image_to_string(Image.open(temp.name))
            logger.info("image text", image_text=msg)
        
        msg = "no text found" if msg == "" else msg
        
        with io.BytesIO(bytes(msg, 'utf-8')) as msg_stream:
            minio_client.put_object("cv-output", f"{filename}.txt", msg_stream, -1, part_size=1024*1024*10)
        return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)