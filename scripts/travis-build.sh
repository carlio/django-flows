#!/bin/bash
python scripts/travis_skip.py

if [ "$?" -eq "0" ]
then
    coverage run django-admin.py test --settings=flows.tests.settings flows
else
    echo "Skipping"
fi
