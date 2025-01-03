
"""Get the OpenReview Forum IDs for the Orals"""

import argparse
import concurrent.futures
import datetime
import json
import os
import pickle
import re
from collections import defaultdict

import openreview
import requests
from tqdm import tqdm

OR_USERNAME = "jkrishna@mit.edu"
# Get the password from the environment variable OR_PASS
OR_PASS = os.environ.get("OR_PASS")

BASEURL = "https://api2.openreview.net"

# Needs to be modified based on the conference
CONFERENCE_NAME = "CoRL 2024"
CONFERENCE_INVITATION = "robot-learning.org/CoRL/2024/Conference/-/Submission"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Add an input file argument. If the argument is not provided, we will download all the notes and save them as a pickle file.
    parser.add_argument(
        "--infile",
        type=str,
        default=None,
        help="path to a pickle file containing notes",
    )

    args = parser.parse_args()

    submissions = []

    try:
        with open(args.infile, "rb") as f:
            submissions = pickle.load(f)
            print(f"Loaded {len(submissions)} notes from {args.infile}")
    except Exception as e:
        print(f"Error loading notes from {args.infile}: {e}")
        print("Downloading all notes from OpenReview...")

        # Initiates the OpenReview client.
        client = openreview.api.OpenReviewClient(
            baseurl=BASEURL, username=OR_USERNAME, password=OR_PASS
        )

        # Get all notes
        submissions = client.get_all_notes(
            invitation=CONFERENCE_INVITATION, details="directReplies"
        )
        # Save as pickle
        # 1. Create directory named "corl2024_notes" if it doesn't exist
        # 2. Save the notes as a pickle file in the directory (pkl file should have datetime in the name)
        # 3. Print the number of notes saved
        if not os.path.exists("corl2024_notes"):
            os.makedirs("corl2024_notes")

        with open(
            f"corl2024_notes/notes_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pkl",
            "wb",
        ) as f:
            pickle.dump(submissions, f)

    # Read the csv file with the paper id to session mapping
    import csv
    paper_id_to_metadata = {}
    oral_session_to_paper = {}
    spotlight_session_to_paper = {}
    poster_session_to_paper = {}
    fixed_paper_id_to_metadata = {}
    with open("corl2024_sessions_list.csv", "r") as f:
        reader = csv.reader(f)
        is_first_row = True
        for row in reader:
            # Skip first row (it is column header)
            if is_first_row:
                is_first_row = False
                continue
            # CSV columns are 'id', 'title', 'authors', 'oral/poster', 'oral session', 'spotlight session', 'poster session'
            paper_id = int(row[0])
            session_key = None
            paper_decision = ""
            if row[3] == "Oral":
                session_key = 4  # Look for oral session column
                paper_decision = "Oral"
            elif row[3] == "Poster":
                session_key = 5  # Look for spotlight session column
                paper_decision = "Poster"
            poster_session_key = 6

            # Create a paper metadata tuple (will later append OR forum link to this)
            paper_metadata = (row[1], row[2], paper_decision, int(row[session_key]), int(row[poster_session_key]))
            paper_id_to_metadata[paper_id] = paper_metadata
            # print(paper_id_to_metadata[paper_id])

            if row[3] == "Oral":
                oral_session = paper_metadata[3]
                if oral_session not in oral_session_to_paper.keys():
                    oral_session_to_paper[oral_session] = []
                oral_session_to_paper[oral_session].append(paper_id)
            elif row[3] == "Poster":
                spotlight_session = paper_metadata[3]
                if spotlight_session not in spotlight_session_to_paper.keys():
                    spotlight_session_to_paper[spotlight_session] = []
                spotlight_session_to_paper[spotlight_session].append(paper_id)
            else:
                print("Error: paper is neither oral nor poster")

            poster_session = paper_metadata[4]
            if poster_session not in poster_session_to_paper.keys():
                poster_session_to_paper[poster_session] = []
            poster_session_to_paper[poster_session].append(paper_id)

    # Get a list of all oral paper IDs
    oral_paper_ids = []
    for oral_session in oral_session_to_paper.keys():
        oral_paper_ids.extend(oral_session_to_paper[oral_session])
    
    # Loop through the submissions and get the forum ID for the oral papers
    oral_paper_id_to_forum_id = {}
    for submission in tqdm(submissions):
        paper_id = submission.number
        if paper_id in oral_paper_ids:
            oral_paper_id_to_forum_id[paper_id] = submission.id
    
    print(f"Found {len(oral_paper_id_to_forum_id)} oral papers")
    print(oral_paper_id_to_forum_id)
    # Write the forum IDs, one per line
    with open("corl2024_oral_forum_ids.txt", "w") as f:
        for forum_id in oral_paper_id_to_forum_id.values():
            f.write(f"{forum_id}\n")
