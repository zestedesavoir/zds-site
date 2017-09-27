#!/bin/bash

cd "$(dirname "$0")"

2to3 --no-diffs --nobackups -w zds *.py scripts/release_generator.py
