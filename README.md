# FPL Scores Calculator 

A project built in Flask that communicates with the Fantasy Premier League Public API, and returns scores formatted in a clear and modern interface. 

Teams and groups are currently hardcoded, but the next step will be setting the project up with PostGres and allowing user group creation!

<img src="app/static/screenshots/Homepage.PNG" >
<img src="app/static/screenshots/Scores.PNG" >

<br>

#### To run this project: 
```
pip3 install -r requirements.txt
python3 app/app.py
````
Then navigate to localhost:5000. 
Deployment to AWS coming imminently!

#### To run tests:
```
pytest
```