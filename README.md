# pysim
CS simulation project for target tracking 

### Requirements

Install Anaconda distribution for python 3. For Windows user, add to your *PATH* the following:

- C:/path/to/Anaconda3
- C:/path/to/Anaconda3/Lib
- C:/path/to/Anaconda3/Scripts


### Installation
- Clone Git repository
- Open conda terminal and type the following commands to create pysim environment

```
conda create --name pysim python=3.6
activate pysim
```

- Install python dependencies (GDAL 2.2.2, PyQt5, mathplotlib, scypy, munkres, timer)

```
conda install gdal pyqt matplotlib scipy munkres scikit-learn
pip install timer
```

- Go to the simplekml folder (in the cloned repository) with the terminal and install it

```
python setup.py install
```



- Copy in folder **pysim/data/carto** (create the folder, if it does not exist), the two following files


  - dnb_land_ocean_ice.2012.3600x1800_geo.tif

### Installation

Go to the **pysim** folder and run:

```
python main.py
```

### Known issues

- If you encounter the error *"This application failed...Available platform plugins are: direct2d, minimal, offscrenn, windows"*, 
add to your *PATH* a new environment variable called QT_PLUGIN_PATH with the following value: c:/path/to/Anaconda3/Library/plugins
