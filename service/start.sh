#!/bin/bash
python -m http.server 81
sudo lsof -t -i:81