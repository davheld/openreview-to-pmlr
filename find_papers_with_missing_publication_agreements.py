"""Create a schedule for the website, including paper links and other metadata for each accepted submission. """

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
CONFERENCE_INVITATION = "robot-learning.org/CoRL/2024/Conference/Submission"


def email_authors(client, submission_info):
    """Use the OR API to email the user."""

    subject = f"[CoRL 2024] Submission #{submission_info['number']} for poster presentation"

    message = f"""Dear {'{{fullname}}'},

    Congratulations again on getting your submission (number {submission_info['number']}) titled "{submission_info['title']}" accepted to CoRL 2024!

    We are pleased to inform you that your paper has been selected for a **poster** presentation during one of the poster sessions. Each poster will also be given a one-minute spotlight talk to attract the audience to come to your poster in the poster session. Spotlight presentations should be given in person. To facilitate rapid back-to-back presentations, authors will provide a 1-minute video which will play muted while they speak. Additional details on poster format and spotlight requirements will be provided on the CoRL 2024 website in the coming weeks.

    Best,
    Pulkit Agrawal, MIT
    Oliver Kroemer, CMU
    Wolfram Burgard, TU Nürnberg
    Krishna Murthy, OpenReview Chair, MIT

    """


    reply_to = "pc@corl.org"
    recipients = submission_info["authors"]

    # client.post_message(
    #     subject=subject, recipients=recipients, message=message, replyTo=reply_to
    # )
    # print(f"{submission_info['decision']} email sent to authors of paper {submission_info['number']}")

    # print(subject)


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

    # Initiates the OpenReview client.
    client = openreview.api.OpenReviewClient(
        baseurl=BASEURL, username=OR_USERNAME, password=OR_PASS
    )

    submissions = []

    try:
        with open(args.infile, "rb") as f:
            submissions = pickle.load(f)
            print(f"Loaded {len(submissions)} notes from {args.infile}")
    except Exception as e:
        print(f"Error loading notes from {args.infile}: {e}")
        print("Downloading all notes from OpenReview...")

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
    accepted_posters = set()
    accepted_orals = set()

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
                accepted_orals.add(paper_id)
            elif row[3] == "Poster":
                session_key = 5  # Look for spotlight session column
                paper_decision = "Poster"
                accepted_posters.add(paper_id)
            else:
                print(f"Invalid paper {paper_id}. Skipping...")
                continue
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

    submission_id_to_or_link = {}
    total_num_of_posters = 0
    num_posters_with_submitted_agreements = 0
    ids_of_missing_spotlights = []
    for submission in submissions:
        invalid_submission = False
        paper_id = submission.number
        # Skip papers that are neither poster nor oral (this shouldn't happen, but FWIW)
        if paper_id not in paper_id_to_metadata.keys():
            continue
        # # Skip orals
        # if paper_id in accepted_orals:
        #     continue
        total_num_of_posters += 1

        if "publication_agreement" not in submission.content.keys():
            ids_of_missing_spotlights.append(paper_id)
        else:
            num_posters_with_submitted_agreements += 1

    print(f"{num_posters_with_submitted_agreements} / {total_num_of_posters} publication agreements submitted. {num_posters_with_submitted_agreements * 100 / total_num_of_posters}%")

