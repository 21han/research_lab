![Pytest](https://github.com/gzhami/research_lab/workflows/Pytest/badge.svg)
![Pylint](https://github.com/gzhami/research_lab/workflows/Pylint/badge.svg)

# research_lab

To help IP and investors visualize and backtest strategies.

# Environment

How to create project environment?

* `conda env create -f env.yml` to create the conda environment for this project.

How to update project environment?

* You should not update project environment often. If you do need to update, 
please follow these steps: 
(1) `rm env.yml` 
(2) use `conda env export --no-builds > env.yml` to update the file 
(3) use `git diff` to check if the change makes sense
(4) contact repo owner to make change `environment` changes
