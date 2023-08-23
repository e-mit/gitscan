#!/bin/bash

rm *.py
# pyuic6 -o test.py test.ui
for file in *.ui ; do
		echo pyuic6 -o ${file/.ui/.py} $file
    pyuic6 -o ${file/.ui/.py} $file
done
