FROM python:3.7.4-alpine3.9
LABEL maintainer="Malte <malte.grimm@openadvice.de>"
LABEL version="0.5.4"
RUN mkdir /scripts /cfg /log
ADD objectserver_exporter.py /scripts
ADD ./cfg/os_exporter_cfg.yml /cfg
RUN pip install prometheus_client requests pyyaml --no-cache-dir
WORKDIR /scripts
CMD [ "python", "./objectserver_exporter.py" ]
