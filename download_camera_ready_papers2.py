import argparse
import json
import os
import pickle
import csv
from collections import defaultdict
from tqdm import tqdm
import openreview
import concurrent.futures
import datetime
import requests

# OR_USERNAME = "jkrishna@mit.edu"
# Get the password from the environment variable OR_PASS
#OR_PASS = os.environ.get("OR_PASS")
OR_USERNAME = ''
OR_PASS = ''

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

    # Initiates the OpenReview client.
    client = openreview.api.OpenReviewClient(
        baseurl=BASEURL, username=OR_USERNAME, password=OR_PASS
    )

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
        if not os.path.exists("corl2024_notes"):
            os.makedirs("corl2024_notes")

        with open(
            f"corl2024_notes/notes_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pkl",
            "wb",
        ) as f:
            pickle.dump(submissions, f)

    if not os.path.exists("corl2024_cameraready_pdfs"):
        os.makedirs("corl2024_cameraready_pdfs")

    # Create a CSV file to store the submission IDs and titles
    with open('submissions.csv', mode='w', newline='') as csv_file:
        fieldnames = ['id', 'title']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for submission in submissions:
            pdf_url = None

            print(f"======== Submission {submission.number} ========")
            submission_info = {}
            submission_info["number"] = submission.number
            submission_info["title"] = submission.content["title"]["value"]

            # Write the id and title to the CSV file
            writer.writerow({'id': submission.number, 'title': submission.content["title"]["value"]})

            for reply in submission.details["directReplies"]:
                invitations = reply["invitations"]
                is_decision = False
                for invitation in invitations:
                    if invitation.endswith("Decision"):
                        submission_info["decision"] = reply["content"]["decision"]["value"]
                        is_decision = True
                        break
            if not is_decision:
                continue

            if "pdf" in submission.content:
                pdf_url = "{0}{1}".format(client.baseurl, submission.content["pdf"])
                paper_number = submission.number
                try:
                    # with  open("corl2024_cameraready_pdfs/Paper{0}.pdf".format(paper_number), "wb") as f:
                        # f.write(client.get_pdf(submission.id))
                    print(f"Saved submission {submission.number}")
                except Exception as e:
                    print(
                        "Error during pdf download for paper number {}, error: {}".format(
                            submission.number, e
                        )
                    )
