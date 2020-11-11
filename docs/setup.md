# Prerequisite

Download conda environment

# Install conda environment

```sh
conda env create -f env.yml
```

This will create a conda enviroment called ResearchLab. Check your conda enviroment list

```sh
conda env list
```

activate the conda environment
```sh
conda activate ResearchLab 
```

# Config environment variable

## Secret key for database
If you are using zsh (usually mac)

```sh
vim ~/.zshrc
```

If you are using bash (usually mac or linux or WSL)

```sh
vim ~/.bashrc
```

Append the following into the bash file
```sh
export DB_SECRET_COMS4156="<YOUR_SECRET_KEY>"
```
e.g.
```sh
export DB_SECRET_COMS4156="abcde12345"
```

Save the file and tyoe if you are using zsh
```sh
source ~/.zshrc
```
OR if you are using bash
```sh
source ~/.bashrc
```

Check your secret key is in the enviroment path
```sh
printenv
```

# Run the app
```sh
python app.py
```
