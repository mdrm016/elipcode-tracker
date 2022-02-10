# Elipcode-Tracker

Torrent private tracker for share content.

## Installation

Install with pip:

```
$ pip install -r requirements.txt
```

## Run Flask
### Run flask for develop
```
$ python app.py
```
In flask, Default port is `5000`

Swagger document page:  `http://127.0.0.1:5000`

### Run flask for production

** Run with gunicorn **

```
$ gunicorn -w 4 -b 127.0.0.1:5000 run:app
```

* -w : number of worker
* -b : Socket to bind


### Run with Docker

```
$ docker build -t flask-example .
$ docker run -p 5000:5000 --name flask-example flask-example 
 
```

