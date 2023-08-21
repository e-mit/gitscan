#!/bin/bash

# pyuic6 -o test.py test.ui
for file in *.ui ; do
    pyuic6 -o ${file/.ui/.py} $file
done
