#!/bin/bash
python scripts/step.py 2
python scripts/FC_change.py
python scripts/KMeanClusters.py
python parser.py Pangatira
python scripts/step2.py