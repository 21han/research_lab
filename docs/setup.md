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

# Run the app
```sh
python app.py
```

I also suggest that we can use the script file which is much easier to configure and run and get rid of some annoying warnings

```sh
chmod +x bin/flaskrun    
```

and run the script:

```sh
./bin/flaskrun
```

