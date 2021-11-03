FROM  jrottenberg/ffmpeg:4.1-ubuntu        

WORKDIR /app

RUN apt-get update && apt-get install -y \
    software-properties-common
RUN add-apt-repository universe
RUN apt-get update && apt-get install -y \
    python3-pip
COPY . /app

RUN pip install -r requirements.txt

ENTRYPOINT [ "python3" ]
