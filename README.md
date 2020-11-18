![Pylint](https://github.com/gzhami/research_lab/workflows/Pylint/badge.svg)

# research_lab

To help algo traders visualize and backtest strategies.

# Environment

How to create project environment?

* `conda env create -f env.yml` to create the conda environment for this project.

How to update project environment?

* You should not update project environment often. If you do need to update, 
please follow these steps: 
(1) `rm env.yml` 
(1.5) make sure you are actually using the correct conda environment
(2) use `conda env export --no-builds > env.yml` to update the file 
(3) use `git diff` to check if the change makes sense
(4) contact repo owner to make change `environment` changes


# Style Check

How to check style?

```
pylint **/*.py
```

# Coverage Check 
To check testing coverage 

```
coverage run  --source=. -m pytest
coverage report 
```
