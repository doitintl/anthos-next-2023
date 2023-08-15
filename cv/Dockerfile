FROM ubuntu:22.10

WORKDIR /app
COPY . ./

RUN apt-get  -qq update && apt-get -qq install -y \
	--no-install-recommends ffmpeg v4l-utils libsm6 libxext6 \
	 python3 python3-pip python3-numpy tesseract-ocr 
RUN pip install -r requirements.txt

CMD ["python3", "main.py"]
