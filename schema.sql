-- Schema for the assignment
CREATE TABLE IF NOT EXISTS tweets (
    tweet_id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    label INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    participant_id TEXT NOT NULL,
    tweet_id TEXT NOT NULL,
    tweet_text TEXT NOT NULL,
    selected_label INTEGER NOT NULL
);