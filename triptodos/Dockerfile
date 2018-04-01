FROM python:3

ENV user mikal
ENV etcd 192.168.50.1:2379

ADD todoist.tgz /opt/script
RUN pip install -e /opt/script/todoist

ADD requirements.txt /opt/script
RUN pip install -U -r /opt/script/requirements.txt

ADD triptodos.py /opt/script
CMD python /opt/script/triptodos.py "${user}" "${etcd}"
