"""Downloads the metadata, paper PDFs, and the supplementary materials from OpenReview."""

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
import sys

# OR_USERNAME = "jkrishna@mit.edu"
# Get the password from the environment variable OR_PASS
#OR_PASS = os.environ.get("OR_PASS")
OR_USERNAME = ''
OR_PASS = ''

BASEURL = "https://api2.openreview.net"

# Needs to be modified based on the conference
CONFERENCE_NAME = "CoRL24"
CONFERENCE_INVITATION = "robot-learning.org/CoRL/2024/Conference/-/Submission"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # Add an input file argument. If the argument is not provided, we will download all the notes and save them as a pickle file.
    parser.add_argument(
        "--infile", type=str, default=None, help="path to a pickle file containing notes",
    	)
    parser.add_argument(
        '-o', '--outdir', default='./', help='directory where data should be saved'
       	)

    args = parser.parse_args()
    outdir = args.outdir

    submissions = []

    # Initiates the OpenReview client.
    client = openreview.api.OpenReviewClient(
        baseurl=BASEURL, username=OR_USERNAME, password=OR_PASS
    )

    # Retrieves the meta data / notes.
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

    # Retrieves the meta data.
    #submissions = client.get_all_notes(
    #    invitation=CONFERENCE_INVITATION)
    submissions_by_forum = {n.forum: n for n in submissions}
    metadata = []
    for forum in submissions_by_forum:
        submission_content = submissions_by_forum[forum].content
        submission_number = submissions_by_forum[forum].number
        print(submission_number)
        forum_metadata = {
            'forum': forum,
            'submission_content': submission_content,
            'submission_number': submission_number
        }
        # only keeps the accepted papers
        venue = submission_content['venue']
        # if venue in ['CoRL 2024 Poster', 'CoRL 2024 Oral']:
        metadata.append(forum_metadata)

    outdir = os.path.join(outdir, CONFERENCE_NAME)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    print('writing metadata to file...')
    # write the metadata, one JSON per line:
    with open(os.path.join(outdir, CONFERENCE_NAME + '__metadata.jsonl'), 'w') as file_handle:
        for k, forum_metadata in enumerate(metadata):
            # print(forum_metadata)
            # print(json.dumps(forum_metadata, indent=2))
            forum = forum_metadata['forum']
            submission_content = forum_metadata['submission_content']
            title = submission_content['title']
            #venue = submission_content['venue'].replace('CoRL 2023 ', '')
            venue = submission_content['venue']
            print('{}\t{}\t{}\thttps://openreview.net/forum?id={}'.format(k, title, venue, forum))
            file_handle.write(json.dumps(forum_metadata) + '\n')


    # Downloads the paper PDFs.
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
                    with  open("corl2024_cameraready_pdfs/Paper{0}.pdf".format(paper_number), "wb") as f:
                       f.write(client.get_pdf(submission.id))
                    print(f"Saved submission {submission.number}")
                except Exception as e:
                    print(
                        "Error during pdf download for paper number {}, error: {}".format(
                            submission.number, e
                        )
                    )
