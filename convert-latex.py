import re

# Mapping of special characters to their LaTeX representations
special_chars = {
    'é': "\\'e",
    'á': "\\'a",
    'í': "\\'i",
    'ó': "\\'o",
    'ú': "\\'u",
    'É': "\\'E",
    'Á': "\\'A",
    'Í': "\\'I",
    'Ó': "\\'O",
    'Ú': "\\'U",
    '\u00f1': "\\~n",  # ñ
    '\u00d1': "\\~N"   # Ñ
}

def convert_to_latex(text):
    """Converts special characters in the text to LaTeX representations."""
    for char, latex in special_chars.items():
        text = text.replace(char, latex)
    return text

# File-based processing
def process_file(input_file, output_file):
    """Reads from input_file, processes text, and writes to output_file."""
    with open(input_file, 'r', encoding='utf-8') as fin:
        input_text = fin.read()

    # Convert all text in the file
    output_text = convert_to_latex(input_text)

    with open(output_file, 'w', encoding='utf-8') as fout:
        fout.write(output_text)

# Main function
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python script.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    process_file(input_file, output_file)
