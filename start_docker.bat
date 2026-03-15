@echo off
echo ==========================================
echo  Bakta Flow Docker Startup
echo ==========================================
echo.
echo Este processo pode levar 15-30 minutos
echo para baixar a base de dados (~1.3GB)
echo.
cd deployment
docker-compose up --build -d
echo.
echo Container iniciado em background!
echo.
echo Para verificar o progresso, execute:
echo   docker logs -f puc-bakta
echo.
echo Para acessar a aplicacao:
echo   http://localhost:5000
echo.
pause
