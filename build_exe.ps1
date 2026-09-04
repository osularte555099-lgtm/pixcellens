python -m pip install -r requirements.txt
pyinstaller --noconfirm --clean --onefile --windowed --name picxellens --copy-metadata streamlit --copy-metadata pywebview --collect-all streamlit --add-data "Dashboard.py;." launch_staff.py
Write-Host "Built dist\picxellens.exe"