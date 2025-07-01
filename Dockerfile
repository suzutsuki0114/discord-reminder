FROM python:3.11-slim 

WORKDIR /app 

COPY bot.py . 
COPY reminder_manager.py . 
COPY env.py .
COPY data/reminders.json ./data/
COPY .env .

RUN apt-get update && \
    apt-get -y install locales tzdata && \
    ln -snf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

RUN echo "ja_JP UTF-8" > /etc/locale.gen && \
    locale-gen && \
    echo "Asia/Tokyo" > /etc/timezone

ENV LANG=ja_JP.UTF-8 

RUN pip install discord.py apscheduler pytz datetime python-dateutil dotenv --break-system-packages 

CMD ["python3", "bot.py"] 
