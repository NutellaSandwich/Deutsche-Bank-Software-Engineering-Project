#!/bin/bash
sudo apt-get install docker.io

sudo service docker start

# pull super-linter image
sudo docker pull github/super-linter

# add the FLASK RUN PORT to .env if it doesn't already exist
if ! grep -q FLASK_RUN_PORT ".env"; then
    echo Creating .env
    echo FLASK_ENV=development >.env
    echo FLASK_RUN_PORT=5123 >> .env
fi

sudo apt-get install python3.10-venv
sudo apt install python3-pip

# add virtual environment if it doesn't already exist
if ! [[ -d vcwk ]]; then
    echo Adding virtual environment 
    python3 -m venv vcwk

    # create pip.conf if doesn't exist
    echo Creating vcwk/pip.conf
    ( cat <<'EOF'
[install]
user = false
EOF
    ) > vcwk/pip.conf

    source vcwk/bin/activate

    echo Setting up Flask requirements
    sudo pip3 install -r requirements.txt
    deactivate
fi

# activate the virtual environment for the coursework
source vcwk/bin/activate

echo Setup complete
