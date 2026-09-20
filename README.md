# Tweet Emotion Labeling Task

A Flask web app for collecting emotion labels for tweets.

## Run locally

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Load the required environment variables from `.env`:

   ```bash
   set -a
   source .env
   set +a
   ```

4. Start the development server:

   ```bash
   flask --app app run --debug
   ```

5. Open `http://127.0.0.1:5000` in a browser.


## Checking Result

User can check the result by adding /results to the URL (e.g., https://127.0.0.1:5000/results)

