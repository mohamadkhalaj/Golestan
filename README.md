# golestanSummeryOfScores
Golestan bot for getting summery of education data.

## Dependencies
Create virtualenvironment and run:
`$ pip3 install -r requirements.txt`

## Installation
- Method 1
```
$ chmod +x run.sh
$ ./run.sh
```
- Method 2
```
$ python3 manage.py makemigrations
$ python3 manage.py migrate
$ python3 manage.py collectstatic --noinput
```

## Run
```
$ python3 manage.py runserver
```

## Super user
```
$ python3 manage.py createsuperuser
```

## API
The only endpoint is `/api/`
### Request method
`POST /api/`
data: `stun=STUDENT_NUMBER&password=STUDENT_PASSWORD`
for avoid rate-limit in order to dedubbing, pass `nolimit=debug` to.
#### simple curl example
`curl 'http://localhost:8000/api/' -X POST -H 'Content-Type: application/x-www-form-urlencoded' --data-raw 'stun=STUDENT_NUMBER&password=STUDENT_PASSWORD&debug=nolimit'`
##### Notice that `debug=nolimit` parameter is optional

## Deploy
Change following confs in `settings.py`
- Replace `SECRET_KEY` with your own
- Make sure `DEBUG` value is `False`
- Replace `*` in `ALLOWED_HOSTS` with your domain
- Uncomment `SECURE_PROXY_SSL_HEADER` and `SECURE_SSL_REDIRECT` for force HTTPS