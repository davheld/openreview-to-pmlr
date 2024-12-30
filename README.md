**Note**: This repository is modifed based on the [original codebase](https://github.com/jietan/openreview-to-pmlr) from Jie Tan. The scripts are updated to support the latest OpenReview APIs. For CoRL 2024, we asked the authors to include the appendices at the end of the camera-ready papers and did not allow uploading other supplementary files. Instead, we provided an option on OpenReview for authors to add a URL link to project websites and additional resources.

# openreview-to-pmlr
These tools are designed to help the CoRL Publication Chair to review camera-ready submissions and to publish proceedings at PMLR (https://proceedings.mlr.press/). It automatically downloads papers from OpenReview and generates the bibtex file for PMLR publication. You can find the bibtex specification here: https://proceedings.mlr.press/spec.html

The code uses CoRL 2024 as an example. Feel free to modify it to suit your needs. No technical support will be provided for this repository.

## To download papers from OpenReview:
```
python download_camera_ready_papers.py
```
You need to change CONFERENCE_NAME and CONFERENCE_INVITATION in the code for your own conference.

## To download the publication agreements (and find papers with missing publication agreements):
```
python download_publication_agreements.py
```

## To generate the bibtex file for PMLR:
```
python create_pmlr_bib.py -i <input_path> -o <output_path>
```
The input_path should point to the folder of pdfs that was generated when you ran download_camera_ready_papers.py. The output_path will contain the corl.bib and all the files that are renamed based on PMLR's requirement.

You need to change CONFERENCE_NAME and ORAL_PAPER_IDS in the code for your own conference. In this file, I assumed that there were two sections: orals and posters. If your conference has only one section or more than two sections, please search for "is_poster" in the code and modify accordingly.

## OLD: To remove mp4 files from the supplementary zip files (note: this was not needed for CORL 2023-2024 because we did not allow authors to submit supplementary files):
```
python del_mp4_from_supp_zip.py -i <path_with_zip_files> -o <output_path>
```
Note that the input zip files will not be altered. All the modified zip files are written to the output_path.
