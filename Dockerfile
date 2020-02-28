FROM amancevice/pandas

WORKDIR /

RUN mkdir scripts

COPY scripts /scripts

RUN apt-get install curl

WORKDIR /scripts
    
RUN curl -o wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh && \
    chmod +x wait-for-it.sh

CMD [ "./wait-for-it.sh", "postgres:5432", "--strict", "--timeout=30", "--", "python", "insertDataFromCSV.py"]