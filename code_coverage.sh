#!/bin/bash

# Get coverage report giving line-by-line missing coverage information

rm .coverage
rm -r .pytest_cache
rm coverage_report.txt
pytest --cov-report=term-missing --cov=gitscan tests > coverage_report.txt
coverage report
