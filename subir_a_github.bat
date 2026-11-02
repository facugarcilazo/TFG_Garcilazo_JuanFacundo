@echo off
echo Subiendo proyecto Maipu Ahorra a GitHub...
git add -A
git commit -m "Actualizacion del proyecto y persistencia en la nube"
git push -u origin main
echo.
echo Proceso finalizado.
pause
