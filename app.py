# This is a Flask server that handles the API request for the emotion labeling task.

import json
import os

from flask import Flask, redirect, render_template, request, session, url_for
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database and data (tweet) file paths
TWEETS_PATH = os.path.join(BASE_DIR, "data", "tweets.json")
DATABASE_URL = os.environ.get("DATABASE_URL")

# Emotion labels used in the task
EMOTIONS = ["Sadness", "Joy", "Love", "Anger", "Fear", "Surprise"]


def database_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required.")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

# Initialize the database with the required tables and insert tweet data if necessary
def initialize_database():
    with open(TWEETS_PATH, encoding="utf-8") as file:
        tweets = json.load(file)

    with database_connection() as connection:
        # Create the tweets table if it doesn't exist
        connection.execute("""
            CREATE TABLE IF NOT EXISTS tweets (
                tweet_id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                label INTEGER NOT NULL
            );
        """)
        # Create the submissions table if it doesn't exist
        connection.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id SERIAL PRIMARY KEY,
                participant_id TEXT NOT NULL,
                tweet_id TEXT NOT NULL,
                tweet_text TEXT NOT NULL,
                selected_label INTEGER NOT NULL
            );
        """)
        with connection.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO tweets (tweet_id, text, label) VALUES (%s, %s, %s) ON CONFLICT (tweet_id) DO NOTHING",
                [(tweet["id"], tweet["text"], tweet["label"]) for tweet in tweets],
            )

# Home page route
@app.get("/")
def home():
    return render_template("home.html")

# 
@app.post("/start")
def start_task():
    participant_id = request.form.get("participant_id", "").strip()

    # No participant ID provided, return to the start page
    if not participant_id:
        return render_template("home.html", error="Enter a participant ID to begin."), 400

    # Check if the participant ID is duplicate
    with database_connection() as connection:
        existing_submission = connection.execute(
            "SELECT * FROM submissions WHERE participant_id = %s LIMIT 1",
            (participant_id,),
        ).fetchone()
        if existing_submission:
            return render_template(
                "home.html", error="This username has already been used. Enter different username."
            ), 400

        # Draw five random tweets from the database for the participant to label
        tweets = connection.execute(
            "SELECT tweet_id, text FROM tweets ORDER BY RANDOM() LIMIT 5"
        ).fetchall()

    # Store the necessary information/data for the user session
    session.clear()
    session["participant_id"] = participant_id
    session["tweets"] = [dict(tweet) for tweet in tweets]
    session["answers"] = {}
    # The index out of 5 randomly selected tweets
    session["index"] = 0
    return redirect(url_for("instructions"))


@app.get("/instructions")
def instructions():
    return render_template("instructions.html")


@app.route("/label", methods=["GET", "POST"])
def label_tweet():
    tweets = session.get("tweets")

    # If no tweets are found in the session, redirect to the home page
    if not tweets:
        return redirect(url_for("home"))

    position = session.get("index", 0)
    if request.method == "POST":
        selected_label = request.form.get("selected_label", type=int)
        # Ensure a valid label is selected
        if selected_label is None or selected_label > len(EMOTIONS) - 1:
            return render_template(
                "label.html", tweet=tweets[position], position=position, emotions=EMOTIONS,
                error="Select one emotion before continuing.",
            ), 400

        # Save the selected label for the tweet and increment the index
        answers = session["answers"]
        answers[tweets[position]["tweet_id"]] = selected_label
        session["answers"] = answers
        position += 1
        session["index"] = position

        # If all tweets have been labeled, save the results and clear the session
        if position == len(tweets):
            with database_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.executemany(
                        "INSERT INTO submissions (participant_id, tweet_id, tweet_text, selected_label) VALUES (%s, %s, %s, %s)",
                        [(session["participant_id"], tweet["tweet_id"], tweet["text"], answers[tweet["tweet_id"]]) for tweet in tweets],
                    )
            session.clear()
            return redirect(url_for("complete"))

    # Render the next index tweet
    return render_template(
        "label.html", tweet=tweets[position], position=position, emotions=EMOTIONS
    )


@app.get("/complete")
def complete():
    return render_template("complete.html")


@app.get("/results")
def results():
    with database_connection() as connection:
        submissions = connection.execute(
            "SELECT participant_id, tweet_text, selected_label FROM submissions"
        ).fetchall()
    return render_template("results.html", submissions=submissions, emotions=EMOTIONS)


initialize_database()


if __name__ == "__main__":
    app.run(debug=True)