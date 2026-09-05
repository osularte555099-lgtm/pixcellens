# Picxellens publish checklist

## 1) Run the desktop app build

From the project folder:

```powershell
python -m PyInstaller PixcellensStaff.spec
```

This creates the packed app in the `dist` folder.

## 2) Share the desktop app with the team

Use the generated EXE in the `dist` folder:

- `dist/PicxellensStaff.exe`

This is the shareable team app.

## 3) Public QR deployment

For customers to scan the QR from personal data, set a public URL before running the server:

```powershell
set PIXCELLENS_PUBLIC_URL=https://picxellens.onrender.com
python server.py
```

or use the launcher:

- `start_picxellens_public.bat`

This only works after the Render service has been created. The public link is then available to customers on personal mobile data or any Wi-Fi network.
## 4) Render deployment

The project already includes `render.yaml` and the app is ready for a Render web service.

Set the environment variables in Render:

- `PIXCELLENS_PUBLIC_URL=https://your-render-app-name.onrender.com`
- `PUBLIC_URL=https://your-render-app-name.onrender.com`

Then deploy the repo.

For a custom domain, add the domain in Render, complete its DNS instructions, and replace both values above with the final `https://` hostname.

The free plan is for testing. Attach a persistent Render Disk mounted at `/var/data` on a paid web service, then set `PIXCELLENS_DATA_DIR=/var/data`. Without that disk or an external database, JSON data can be lost when the service restarts.

## 5) Final verification

- QR code uses the public URL instead of local Wi‑Fi IP
- Staff app connects to the same public backend
- EXE is built successfully and can be shared with the team
