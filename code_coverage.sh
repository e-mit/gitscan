#!/bin/bash

# Get coverage report giving line-by-line missing coverage information

rm -r .coverage
rm -r .pytest_cache
pytest --cov-report=term-missing --cov=gitscan tests > coverage_report.txt
coverage report
