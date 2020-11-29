# Setup

## changelog

(2020-11-29) changed from `conda` to `pip`.

## Steps

1. make sure you have read this [post](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html)
2. use `virtualenv` to create an environment for `research_lab` project.
3. use `pip install -r requirements.txt` to install package inside the new environment.
4. for updating environment, please use `pip freeze > requirement.txt` and verify if the change makes sense by running `git diff`.
 