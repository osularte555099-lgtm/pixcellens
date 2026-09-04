# picxellens

Photo shop queue system with two customer intake paths:

- **Student**: full name, section, student ID, grade/year level, phone, and Gmail or school Gmail.
- **Walk-in**: full name, Gmail, and phone number.

## Run locally

```powershell
python -m pip install -r requirements.txt
$env:PICXELLENS_PUBLIC_URL = "http://YOUR-COMPUTER-LAN-IP:8501"
python -m streamlit run Dashboard.py
```

Staff use the dashboard at `/?view=staff`. Customers use `/?view=student` or `/?view=walkin`, normally by scanning the QR codes shown in **QR codes**.

For phone scanning on the same Wi-Fi, replace `YOUR-COMPUTER-LAN-IP` with the staff computer's IPv4 address and run Streamlit with `--server.address=0.0.0.0 --server.port=8501`.

## Deploy free on Render

1. Push this repository to GitHub.
2. In Render, choose **New +** -> **Blueprint** and select the `picxellens` repository.
3. Set `PICXELLENS_PUBLIC_URL` to the deployed Render URL, for example `https://picxellens.onrender.com`.
4. Deploy. Render uses the included `render.yaml` and its free web service plan.

The free service can sleep when unused, so the first request after inactivity may take a moment. SQLite is local to the service and can be reset when Render rebuilds or replaces the instance; use a hosted database before relying on this for permanent production records.

## Build the staff app

Run `build_exe.ps1`. The desktop app is created at `dist\picxellens.exe`; it opens the staff dashboard in its own window. The SQLite queue database is stored beside the app script while developing, or in the executable's working directory when packaged.