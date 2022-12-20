# première image docker, nommée "build" : sert à compiler tesserac avec toutes les optimisations qui vont bien
# basé sur https://tesseract-ocr.github.io/tessdoc/Compiling.html#linux
FROM debian:bookworm as build


RUN    DEBIAN_FRONTEND=noninteractive \
       apt-get update -y \
    && apt-get install -y git libtool clang make automake autoconf pkg-config libpng-dev libjpeg-dev libtiff5-dev zlib1g-dev libleptonica-dev

WORKDIR /opt/src

# clone sans historique, uniquement les versions de la version 5.2.0
RUN git clone https://github.com/tesseract-ocr/tesseract.git --depth 1 --branch 5.2.0 --single-branch

# --enable-static --disable-shared pour 
# --disable-openmp
# --disable-graphics
RUN    cd tesseract \
    && ./autogen.sh \
    && ./configure --disable-openmp --disable-graphics --enable-static --disable-shared \
    && make \
    && make install

# second image : c'est cette image qui sera utiliser.
FROM debian:bookworm

EXPOSE 8888

WORKDIR /opt/tesseract_server

# installation de python, libjemalloc et ... tesseract-ocr
# pour tesseract-ocr: cela permet d'installer toutes les dépendances de tesseract-ocr (qui sont aussi l'image "build" mais pour les retrouver dans /usr/lib ...)
# pour libjemalloc: cela réduit la consommation mémoire, voir https://zapier.com/engineering/celery-python-jemalloc/
#                   j'avoue ne pas avoir tester sans.
RUN    DEBIAN_FRONTEND=noninteractive \
       apt-get update -y \
    && apt-get install -y python3 python3-pip tesseract-ocr tini libjemalloc2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# copie de tesseract de l'image "build"
COPY --from=build /usr/local/bin /usr/local/bin/
COPY --from=build /usr/local/lib /usr/local/lib/
COPY --from=build /usr/local/share/tessdata /usr/local/share/tessdata/

# efface le tesseract installé par le paquet debian "tesseract-ocr" 
RUN    rm /usr/bin/tesseract \
    && rm /usr/lib/x86_64-linux-gnu/libtesseract.so.5 \
    && rm /usr/lib/x86_64-linux-gnu/libtesseract.so.5.0.1 \
    && mv /usr/share/tesseract-ocr/5/tessdata/*.traineddata /usr/local/share/tessdata/

# 
COPY requirements.txt .

RUN pip install -r requirements.txt

# 
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2

COPY . .

CMD [ "tini", "--", "/usr/bin/python3", "-m", "tesseract_server", "--production", "--host", "0.0.0.0"]
