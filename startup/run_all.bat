@echo off
REM Change to the Websockets directory
cd /d C:\Users\luukm\Documents\GitHub\Websockets

REM Run server.py in the background
start "" python server.py

REM Run intermediateClient.py in the background
start "" python intermediateClient.py

REM Run recieverClient.py in a new terminal window
start cmd /k python recieverClient.py

REM Run the shell script from the startup folder
cd startup
bash starthume.sh
