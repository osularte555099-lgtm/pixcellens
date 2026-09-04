python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --onefile --windowed --name picxellens --add-data "Dashboard.py;." launch_staff.py
Write-Host "Built dist\picxellens.exe"