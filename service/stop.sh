#!/bin/bash
sudo lsof -t -i:81
kill -9 $(lsof -t -i:81)