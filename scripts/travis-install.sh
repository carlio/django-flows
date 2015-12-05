#!/bin/bash
python scripts/travis_skip.py

if [ "$?" -eq "0" ]
then
    pip install coverage coveralls django-nose
    pip install --editable .
    pip install $DJANGO
else
    echo "Skipping"
fi
