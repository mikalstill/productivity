FROM python:2

ENV user mikal
ENV etcd 192.168.50.1:2379

ADD tripit /opt/script
ADD tripit.py /opt/script

ADD requirements.txt /opt/script
RUN pip install -U -r /opt/script/requirements.txt

ADD tripit_scraper.py /opt/script
CMD python /opt/script/tripit_scraper.py "${user}" "${etcd}"
