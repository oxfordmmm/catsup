# Catsup

Catsup is the upload client for SP3.

<img src="https://i.imgur.com/6m0unoK.png" width=250> <img src="https://i.imgur.com/T7jLKkN.png" width=250> <img src="https://i.imgur.com/3EGU1bk.png" width=250> <img src="https://i.imgur.com/UYZodNw.png" width=250> <img src="https://i.imgur.com/JCrFAg8.png" width=250>

## Supported operating systems

- Linux
- OS X
- Windows 10 WSL

## Requirements

- Minimum 16G ram
- Minimum 20G disk space on your home directory partition

## Installation

```curl https://raw.githubusercontent.com/oxfordmmm/catsup/master/install.bash | bash```

This will install conda and the application dependencies into your home directory.

After installation, please close the terminal and open a new one to ensure that conda is initialized.

## using the web UI

Go to the ~/catsup directory and run

```bash run.bash```

This will open a web browser to http://127.0.0.1:8080

## Alternative configurations

catsup can be run as a command-line program to support automated deployments. Please see README.md.old for generic information and user_guide.md for specific setup instructions.
