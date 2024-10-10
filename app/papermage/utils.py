from papermage.magelib import Entity, Box, Document
import hashlib
from typing import List, Optional, Dict, Tuple
import logging

### --- CONSTANTS --- ###

WRAP_ROWS = True
PARAGRAPH = 'par'
SECTION = 'sec'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#log via file
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

### --- PAPERMAGE UTILITY FUNCTIONS --- ###

def concatenate_texts(layer : List[Entity], remove_newline_chars = True) -> str:
    """concatenate all text blocks in a layer."""
    text = "".join([entity.text.strip() for entity in layer])
    if remove_newline_chars:
        text = text.replace('- ', '')
    return text

def extract_paper_info(page : Entity) -> Tuple[str, str, str, str]:
    """Extracts Title, Authors, Abstract and Keywords from the given page of the document."""
    title = concatenate_texts(page.intersect_by_box('titles'))
    authors = 'Paper Authors: ' + concatenate_texts(page.intersect_by_box('authors'))
    abstract = concatenate_texts(page.intersect_by_box('abstracts'))
    abstract = 'Paper Abstract: ' + abstract if 'abstract' not in abstract.lower() else abstract
    keywords = concatenate_texts(page.intersect_by_box('keywords'))
    keywords = 'Paper Keywords: ' + keywords if 'keywords' not in keywords.lower() else keywords
    return(title, authors, abstract, keywords)

# this is an example of word wrap-
# ping, which is a common occurence.
def wrap_rows(first_row : Entity, sec_row : Entity) -> Tuple[Entity, Entity]:
    """wraps the first_row that ends with some_wo- and the sec_row that starts with rd."""
    first_row_words = first_row.text.split(' ')
    sec_row_words = sec_row.text.split(' ')
    wrapped_word = first_row_words[-1].replace('-', '').strip() + sec_row_words[0]
    first_row_words[-1] = wrapped_word # replace last word of first row with wrapped word
    sec_row_words.pop(0) # remove first word of second row
    first_row.text = ' '.join(first_row_words).rstrip()
    sec_row.text = ' '.join(sec_row_words).rstrip()
    return (first_row, sec_row)

def extend_box(ent : Entity, amount : float) -> Entity:
    """Returns a copy of the entity with a box extended upwards and downwards by amount."""
    ext_ent = Entity(spans=ent.spans.copy(), boxes=ent.boxes.copy(), 
                     images=ent.images.copy(), metadata=ent.metadata)
    # coordinates are relative to the page size
    json_box = ent.boxes[0].to_json()
    json_box[1] = json_box[1] - amount if json_box[1] - amount > 0 else 0 # extend box upwards
    json_box[3] = json_box[3] + amount*2 if json_box[3] + amount*2 < 1 else 1 # extend box downwards
    new_box = Box.from_json(json_box)
    ext_ent.boxes = [new_box]
    return ext_ent

def filter_preliminary_row(row : List[Entity], page : Entity) -> bool:
    """Returns True if row intersects Titles, Abstracts, Authors and keywords from the page."""
    row_box : Box = row.boxes[0]
    return any([row_box.is_overlap(fig.boxes[0]) for fig in page.intersect_by_box('titles')]) \
    or any([row_box.is_overlap(tab.boxes[0]) for tab in page.intersect_by_box('authors')]) \
    or any([row_box.is_overlap(tab.boxes[0]) for tab in page.intersect_by_box('abstracts')]) \
    or any([row_box.is_overlap(tab.boxes[0]) for tab in page.intersect_by_box('keywords')]) \

def filter_row(row : Entity, page : Entity) -> bool:
    """Returns True if row intersects any figure, table or equation from the page."""
    # check if the paragraph is in the body of the paper
    row_box : Box = row.boxes[0]
    return any([row_box.is_overlap(fig.boxes[0]) for fig in page.intersect_by_box('figures')]) \
    or any([row_box.is_overlap(tab.boxes[0]) for tab in page.intersect_by_box('tables')]) \
    or any([row_box.is_overlap(cap.boxes[0]) for cap in page.intersect_by_box('captions')]) \
    or any([row_box.is_overlap(eq.boxes[0]) for eq in page.intersect_by_box('equations')]) \
    or any([row_box.is_overlap(foot.boxes[0]) for foot in page.intersect_by_box('footers')]) \
    or any([row_box.is_overlap(foot.boxes[0]) for foot in page.intersect_by_box('footnotes')]) \
    or any([row_box.is_overlap(head.boxes[0]) for head in page.intersect_by_box('headers')])

def get_section(doc : Document, row : Entity) -> Optional[Entity]:
    """Returns the section that intersects with the row, None Otherwise."""
    sections = doc.intersect_by_box(row, 'sections')
    return sections[0] if len(sections) > 0 else None

def convert_rows_to_markdown(doc : Document, proc_rows : List[Dict[str,str|Entity]]) -> str:
    """Converts extracted rows into markdown format."""
    content = ''
    title, authors, abstract, keywords = extract_paper_info(doc.pages[0])
    content += f"# {title}\n\n"
    content += f"{authors}\n\n"
    content += f"{abstract}\n\n"
    content += f"{keywords}\n"
    for row_idx, row in enumerate(proc_rows):

        row_tipe = row['type']
        row_ent = row['entity']

        if row_tipe == SECTION:
            content += f"\n## {row_ent.text}\n\n"

        elif row_tipe == PARAGRAPH:
            if WRAP_ROWS:
                if row_ent.text.endswith('-'):
                    try:
                        next_row = proc_rows[row_idx + 1]['entity']
                        cur, next = wrap_rows(row_ent, next_row)
                        proc_rows[row_idx]['entity'] = cur # for consistency
                        proc_rows[row_idx + 1]['entity'] = next # update next row
                    except IndexError as e:
                        print(f"WRAPPING ROWS: NO NEXT ROW FOUND - {e}")
                        continue
                # wrap "wo- \n rd" sequences in "word" 
            content += f"{row_ent.text}\n"

    logger.info("FINISHED PROCESSING EXTRACTED ROWS")
    return content

def process_document(doc : Document) -> None:
    """Converts document into markdown format."""

    ref_rows : List[Entity] = [] # content of the references section
    found_ref = False

    proc_rows : List[Dict[str,str|Entity]] = []
    image_data : List

    for page_idx, page in enumerate(doc.pages):

        logger.info(f"PROCESSING PAGE {page_idx}")
        page_rows = [x for x in page.intersect_by_span('rows')]
        page_figs =  page.intersect_by_box('figures')
        logger.debug(f"FOUND {len(page_rows)} ROW(s) AND {len(page_figs)} FIGURE(s) IN PAGE {page_idx}")

        #extract image data from the page
        for fig in page_figs:
          # TODO extract figure id (such as Fig.1), extract figure caption and metadata
            pass

        # extract text data from the page
        for row_idx, row in enumerate(page_rows):
            # skipping rows that belong to preliminary or additional paper sections
            if filter_preliminary_row(row, page) or filter_row(row, page):
                continue
            # check if row belongs to a section, if so, add the section to the processed rows
            if section := get_section(doc, row):
                if found_ref:
                    logger.info(f"FOUND NEW SECTION AFTER REFERENCES - STOPPING")
                    break
                if section not in [entry['entity'] for entry in proc_rows if entry['type'] == SECTION]:
                    if any(sub in section.text.lower() for sub in ['reference', 'citation', 'bibliograph']):
                        logger.debug(f"FOUND REFERENCES PARAGRAPH ON PAGE {page_idx}")
                        found_ref = True
                        continue
                    logger.debug("ADDED SECTION ", section.text)
                    proc_rows.append( {'type':SECTION, 'entity':section} )
                continue
            
            if found_ref:
                ref_rows.append(row)
            else:
                proc_rows.append( {'type':PARAGRAPH, 'entity':row} )

    # convert processed rows into markdown format
    markdown_content = convert_rows_to_markdown(doc, proc_rows)
    return markdown_content


### --- APP UTILITY FUNCTIONS --- ###

def calculate_hash(content : bytes, buffer_size : int = 4096) -> str:
    """Returns the truncated hash of the content using a buffer with `buffer_size` chunks."""
    hash_obj = hashlib.md5()
    for i in range(0, len(content), buffer_size):
        chunk = content[i:i+buffer_size]
        hash_obj.update(chunk)
    full_hash = hash_obj.hexdigest()
    truncated_hash = full_hash[:len(full_hash)//2]
    return truncated_hash