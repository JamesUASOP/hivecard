# HiveCard

HiveCard is a mobile simulation tool that runs software-in-the-loop (SITL) aircraft on a Raspberry Pi and broadcasts them over WiFi for QGroundControl and other GCS apps.

## Documentation (online)

**Read the instructions anytime — no HiveCard device required:**

**https://jamesuasop.github.io/hivecard/**

Topics include getting started, starting aircraft, connecting QGroundControl, managing locations, settings, and troubleshooting.

When connected to a HiveCard device, you can also open on-device help at `http://hivecard/help` or the **Help** tab in the web app.

## Web GUI

Flask app in this repository (`app.py`) serving the fleet dashboard on port **8080**.

Default login (change in Settings after first sign-in):

- Username: `hivecard`
- Password: `hivecard`

### Setup on Raspberry Pi

1. Copy this folder to the Pi (e.g. `/home/uasop/hivecard-web/`).
2. Copy `config.json.example` to `config.json` and set credentials.
3. Install dependencies: `pip install -r requirements.txt`
4. Run or install as a user systemd service (`hivecard-web.service`).

Deploy scripts for captive portal and WiFi SSID controls are in `deploy/`.

## Rebuild GitHub Pages docs

After editing help content in `templates/docs/sections/`:

```bash
pip install Jinja2
python scripts/build_gh_pages.py
git add docs/
git commit -m "Update documentation site"
git push
```

GitHub Pages serves the static site from the `/docs` folder on the `main` branch.

## Video placeholders

Add YouTube URLs in `data/videos.json`, then rebuild the docs site and restart the web app on the device.

## License

See repository license file if present.
