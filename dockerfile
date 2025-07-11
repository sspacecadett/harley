FROM python:latest
LABEL Maintainer="harleydocker"

ENV PYTHONPATH "${PYTHONPATH}:/home/midas/Documents/PYTHONPATH/bin/activate"

WORKDIR /home/midas/Documents/scripts/harley

COPY harley.py ./

RUN pip install discord dotenv

CMD [ "python", "./harley.py"]