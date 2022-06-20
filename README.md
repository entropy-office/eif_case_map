# eif-submit

## Project

This dashboard provides an interactive visualization of the location and intervention aspects of various early intervention case studies, as provided by the Early Intervention Foundation (EIF). 

## Code

### Run dashboard

To run the dashboard, use: 

``` bash
docker-compose build
docker-compose up
```

and then navigate to the port `http://0.0.0.0:80`

### Project structure

* `app/` - All scripts, assets and data related to the dashboard
* `eif_case_map_venv/` - Python virtual environment
* `.env` - Environment variables for application services
* `docker-compose.yml` - Docker compose file
* `Dockerfile` - Docker file

### Contributing

To contribute to this project, please also update the virtual environment. 
You can activate the python venv with: 

``` bash
source eif_case_map_venv/bin/activate
```

Any new dependencies should be install within this environment with something like: 

``` bash
pip3 install foo
```
If any new dependencies are added, please include them in the `app/requirements.txt` with: 

``` bash
pip3 freeze > app/requirements.txt
```