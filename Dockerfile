FROM snakepacker/python:modern

RUN python3 -m virtualenv --python=/usr/bin/python3.7 /opt/venv

WORKDIR /app

COPY ./KristaBackup/web ./web
COPY ./KristaBackup/core ./core
COPY ./KristaBackup/common ./common
COPY ./KristaBackup/lib ./lib
COPY ./KristaBackup/KristaBackup.py ./KristaBackup/_version.py ./KristaBackup/requirements.txt ./


RUN /opt/venv/bin/pip3 install -r requirements.txt
RUN /opt/venv/bin/pip3 install pyinstaller

CMD /opt/venv/bin/python3 -O -m PyInstaller --onefile \
  --noconfirm --nowindow \
  --add-data 'web/webapp/templates:templates' \
  --add-data 'web/webapp/static:static' --distpath '/build' \
  --hidden-import pkg_resources.py2_warn \
  KristaBackup.py
