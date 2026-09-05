# Picxellens

Picxellens customer registration form and staff queue application.

## Publish a public customer link

The included Render configuration publishes the app on the internet so customers can open it using mobile data or any Wi-Fi network.

1. Push this folder to a GitHub repository.
2. Create a Render account at [render.com](https://render.com) and choose **New > Blueprint**.
3. Select the repository and deploy the included `render.yaml`.
4. Open the Render service URL, for example `https://picxellens.onrender.com`.
5. Use that URL in the staff QR code. Customers can now scan it from any network.

To use your own domain, add it in Render under **Settings > Custom Domains**, then set both `PIXCELLENS_PUBLIC_URL` and `PUBLIC_URL` to the HTTPS domain.

The free Render service is suitable for testing and can sleep when idle. For production records, configure `PIXCELLENS_DATA_DIR` to a persistent Render Disk mount such as `/var/data`, or move the records to an external database. The app now uses atomic writes and will keep registrations in that configured data directory.

## Mobile-data QR access

For customers to scan the QR code while on personal data instead of the same Wi‑Fi, run the app with a public URL in the environment, for example:

PIXCELLENS_PUBLIC_URL=https://picxellens.onrender.com

or:

PUBLIC_URL=https://picxellens.onrender.com

Then the QR link will point to the public host instead of the local network IP.