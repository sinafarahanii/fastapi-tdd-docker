# UserShift-Log

## Description

Welcome to this project! This project is about handling common HTTP request and the difference between their APIs using FastAPI.
FastAPI is a modern, high performance, easy to use web framework for building APIs.

## Install

Note: It is assumed that you have python and docker installed on your system.

In order to use pip commands, you can make a virtual environment in your directory by running:

    python -m venv venv
then activate it by running: (on windows)

    venv\Scripts\activate.bat
    
Required packages are mentioned in `requriements.txt`.

    pip install -r requirements.txt
    
## Run the app

 Make suire that docker is running on your system.

In the path that `docker-compose.yml` is placed, run this command:

    docker-compose build
After it's done (it might take few minutes), run this command:

    docker-compose up -d
You should see that the two containers are running(You can check if they are running via docker desktop too).
if not run the above command again.

FastAPI provides you a client to test API requests in your project: <a href="http://127.0.0.1:8004/docs#/">`http://127.0.0.1:8000/docs#/`


## Test each method

You can test each method and each possible case by test functions provided in `test_api.py`.You can also can run all the tests at once by running:

        python test_api.py
