@echo off
cd /d %~dp0
set PUB_CACHE=C:\dev\pub-cache
C:\devlutterinlutter.bat run -d web-server --web-port 3100 --web-hostname localhost --dart-define=API_URL=http://localhost:8000
