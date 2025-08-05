# Installation Guide

Follow these steps to install and set up the ScoShow application on a new computer:

## Prerequisites
1. Ensure Python 3.7 or higher is installed on your system.
   - Download Python from [python.org](https://www.python.org/downloads/).
   - During installation, check the box to add Python to your PATH.

2. Install Git (optional, for version control).
   - Download Git from [git-scm.com](https://git-scm.com/).

## Steps

### 1. Clone the Repository
If you have Git installed, clone the repository:
```powershell
git clone https://github.com/jakeliedo/ScoShow.git
```
Otherwise, download the repository as a ZIP file from GitHub and extract it.

### 2. Navigate to the Project Directory
Open a terminal and navigate to the project folder:
```powershell
cd path\to\ScoShow
```

### 3. Set Up a Virtual Environment
Create and activate a virtual environment:
```powershell
python -m venv ven
ven\Scripts\activate
```

### 4. Install Dependencies
Install the required Python packages:
```powershell
pip install -r requirements.txt
```

### 5. Run the Application
Start the application:
```powershell
python main.py
```

## Notes
- Ensure all necessary libraries are installed using `requirements.txt`.
- If you encounter issues, verify Python and pip versions using:
```powershell
python --version
pip --version
```

## Optional: Package Installation
To install the application as a package:
1. Build the package:
```powershell
python setup.py sdist bdist_wheel
```
2. Install the package:
```powershell
pip install dist/ScoShow-1.0.0-py3-none-any.whl
```
