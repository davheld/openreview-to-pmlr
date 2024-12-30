import argparse
import os
import json
import shutil

# Modifies the following CONSTANTS based on your need.
CONFERENCE_NAME = 'corl24'
CONFERENCE_YEAR = '24'
ORAL_PAPER_IDS = [
]
PDF_FOLDER = 'corl2024_cameraready_pdfs'

# Customizes the header of the bibtex based on your conference information.
def write_proceeding_info():
    bibtex_str = '@Proceedings{CoRL-2023,\n'
    bibtex_str += '\tbooktitle = {Proceedings of The 8th Conference on Robot Learning},\n'
    bibtex_str += '\tname = {Conference on Robot Learning},\n'
    bibtex_str += '\tshortname = {CoRL},\n'
    bibtex_str += '\tyear = {2024},\n'
    bibtex_str += '\teditor = {Agrawal, Pulkit and Kroemer, Oliver and Burgard, Wolfram},\n'
    bibtex_str += '\tvolume = {},\n'
    bibtex_str += '\tstart = {2024-11-06},\n'
    bibtex_str += '\tend = {2024-11-09},\n'
    bibtex_str += '\taddress = {Munich, Germany},\n'
    bibtex_str += '\tconference_url = {https://2024.corl.org/},\n'
    bibtex_str += '\tconference_number={8},\n'
    bibtex_str += '}\n\n'
    return bibtex_str

def create_identifiers(all_metadata):
    '''Creates the identifiers based on lastnameYY. If two papers share the same identifier, one alphabet is appended.'''
    ids = []
    unique_id_set = set()
    collision_id_count_dict = {}

    for i, metadata in zip(range(len(all_metadata)), all_metadata):
        #print(metadata['submission_content'].get('authors', 'No authors field'))
        authors = metadata['submission_content'].get('authors', {}).get('value', [])
        identifier = (authors[0].split(' ')[-1]).lower() + CONFERENCE_YEAR
        #identifier = (metadata['submission_content']['authors'][0].split(' ')[-1]).lower() + '23'
        paper_title = metadata['submission_content']['title']
        if identifier in unique_id_set:
            print('conflict found!', i, identifier, paper_title)
            collision_id_count_dict[identifier] = 0
        unique_id_set.add(identifier)
        ids.append(identifier)
    for i in range(len(ids)):
        if ids[i] in collision_id_count_dict.keys():
            collision_id_count_dict[ids[i]] += 1
            ids[i] = ids[i] + chr(ord('a') + collision_id_count_dict[ids[i]] - 1)
    return ids

def get_pdf_page_length(pdf_file_name):
    # linux
    # cmd = "pdfinfo " + pdf_file_name + " | grep 'Pages' | awk '{print $2}'"
    # Mac systems
    cmd = "mdls -raw -name kMDItemNumberOfPages " + pdf_file_name
    paper_length = int(os.popen(cmd).read().strip())
    print(pdf_file_name, paper_length)
    return paper_length

def create_paper_bibtex(indir, outdir, identifier, metadata, is_poster, page_start=1):
    '''Creates a bibtex entry for one paper.'''
    title = metadata['submission_content']['title']
    abstract = metadata['submission_content']['abstract']
    submission_number = metadata['submission_number']
    paper_length = get_pdf_page_length(os.path.join(PDF_FOLDER, 'Paper' + str(submission_number) + '.pdf'))
    authors = metadata['submission_content']['authors']
    openreview = metadata['forum']
    bibtex_str = serialize_to_bibtex(identifier, title, abstract, authors, page_start, paper_length, openreview, is_poster)
    rename_files(indir, outdir, metadata, identifier, submission_number)
    return bibtex_str, page_start + paper_length

def format_author_names(authors):
    author_names = ''
    authors = authors['value']
    for name in authors:
        splitted_name = name.split(' ')
        last_name = splitted_name[-1]
        first_name = name[0:len(name)-len(last_name)-1]
        author_names += last_name + ', ' + first_name
        if name != authors[-1]:
            author_names += ' and '
    return author_names

def rename_files(indir, outdir, metadata, bibtex_str, submission_number):
    '''Renames the files from OpenReview-id.pdf to identifier.pdf.'''
    src_folder = PDF_FOLDER
    dest_folder = outdir
    pdf_name = 'Paper' + str(submission_number) + '.pdf'
    new_name = bibtex_str + '.pdf'
    print('rename pdf: {}->{}'.format(pdf_name, new_name))

    shutil.copyfile(os.path.join(src_folder, pdf_name), os.path.join(dest_folder, new_name))

    # if 'supplementary_material' in metadata['submission_content'].keys() and metadata['submission_content']['supplementary_material'] != "":
    #    if not metadata['submission_content']['supplementary_material']['value'].endswith('.zip'):
    #        print (metadata['submission_content']['supplementary_material'])
    #        raise ValueError
    #   supplementary_name = metadata['forum'] + '_supp.zip'
    #    new_supp_name = bibtex_str + '-supp.zip'
    #    print('rename supp: {}->{}'.format(supplementary_name, new_supp_name))
    #    shutil.copyfile(os.path.join(src_folder, supplementary_name), os.path.join(dest_folder, new_supp_name))

def serialize_to_bibtex(identifier, title, abstract, authors, page_start, paper_length, openreview, is_poster):
    bibtex_str = '@InProceedings{'
    bibtex_str += identifier + ',\n'
    bibtex_str += '\ttitle = {' + title['value'] + '},\n'
    #if is_poster:
    #    bibtex_str += '\tsection = {Poster},\n'
    #else:
    #    bibtex_str += '\tsection = {Oral},\n'
    bibtex_str += '\tauthor = {' + format_author_names(authors) + '},\n'
    bibtex_str += '\tpages = {' + str(page_start) + '-' + str(page_start + paper_length - 1) + '},\n'
    bibtex_str += '\topenreview = {' + openreview + '},\n'
    bibtex_str += '\tabstract = {' + abstract['value'] + '}\n'
    
    # Add software link if available
    software_link = metadata['submission_content'].get('code')
    if software_link and software_link.get('value'):
        bibtex_str += '\tsoftware = {' + software_link['value'] + '},\n'    
    
    # Add video link if available
    video_link = metadata['submission_content'].get('video')
    if video_link and video_link.get('value'):
        bibtex_str += '\tvideo = {' + video_link['value'] + '},\n'

    bibtex_str += '}\n\n'
    return bibtex_str

def read_paper_metadata(filename):
    paper_metadata = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        for line in lines:
            data = json.loads(line)
            paper_metadata.append(data)
    print('Total number of papers: {}'.format(len(paper_metadata)))
    return paper_metadata

def split_metadata_and_identifiers(all_metadata, all_identifiers):
    '''Splits the metadata and identifiers based on sections. In CoRL 2023, there are two sections: oral and poster.'''
    oral_metadata = []
    poster_metadata = []
    oral_identifiers = []
    poster_identifiers = []
    for metadata, identifier in zip(all_metadata, all_identifiers):
        forum_id = metadata['forum']
        if forum_id in ORAL_PAPER_IDS:
            oral_metadata.append(metadata)
            oral_identifiers.append(identifier)
        else:
            poster_metadata.append(metadata)
            poster_identifiers.append(identifier)
    print("num orals: {}, num posters: {}".format(len(oral_metadata), len(poster_metadata)))
    return oral_metadata, poster_metadata, oral_identifiers, poster_identifiers


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-i', '--indir', default='./', help='input directory that contains the metadata, pdfs and supplementary files.')
    parser.add_argument(
        '-o', '--outdir', default='./out', help='directory where data should be saved')

    args = parser.parse_args()
    indir = args.indir
    outdir = args.outdir
    if not os.path.exists(outdir):
        os.makedirs(outdir) 

    # Reads metadata and construct identifiers. Split them into the oral and poster sections.
    page_start = 1
    metadata = read_paper_metadata(os.path.join(indir, CONFERENCE_NAME + '__metadata.jsonl'))
    identifiers = create_identifiers(metadata)
    oral_metadata, poster_metadata, oral_identifiers, poster_identifiers = split_metadata_and_identifiers(metadata, identifiers)

    # Writes the bibtex into the file, and rename the files into identifier.pdf or identifier-supp.zip.
    with open(os.path.join(indir, CONFERENCE_NAME + '.bib'), 'w') as f:
        bibtex = write_proceeding_info()
        f.write(bibtex)
        for identifier, metadata in zip(oral_identifiers, oral_metadata):
            bibtex, page_start = create_paper_bibtex(indir, outdir, identifier, metadata, is_poster=False, page_start=page_start)
            f.write(bibtex)
        for identifier, metadata in zip(poster_identifiers, poster_metadata):
            bibtex, page_start = create_paper_bibtex(indir, outdir, identifier, metadata, is_poster=True, page_start=page_start)
            f.write(bibtex)
