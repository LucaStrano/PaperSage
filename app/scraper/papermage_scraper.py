from app.scraper.scraper import Scraper, ImageData

from typing import List, Tuple, Optional, Dict
from papermage.magelib import Entity, Box, Document
from papermage.recipes import CoreRecipe
from PIL import Image
import io
import fitz
import logging

class PapermageScraper(Scraper):

    def __init__(self):
        super().__init__()
        self.WRAP_ROWS = True
        self.PARAGRAPH = 'par'
        self.SECTION = 'sec'
        self.zoom_factor = 2
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        #log via file
        self.fh = logging.FileHandler('papermage_scraper.log')
        self.fh.setLevel(logging.DEBUG)
        self.logger.addHandler(self.fh)

    def concatenate_texts(self, layer : List[Entity], remove_newline_chars = True) -> str:
        """concatenate all text blocks in a layer."""
        text = "".join([entity.text.strip() for entity in layer])
        if remove_newline_chars:
            text = text.replace('- ', '')
        return text

    def extract_paper_info(self, page : Entity) -> Tuple[str, str, str, str]:
        """Extracts Title, Authors, Abstract and Keywords from the given page of the document."""
        title = self.concatenate_texts(page.intersect_by_box('titles'))
        authors = 'Paper Authors: ' + self.concatenate_texts(page.intersect_by_box('authors'))
        abstract = self.concatenate_texts(page.intersect_by_box('abstracts'))
        abstract = 'Paper Abstract: ' + abstract if 'abstract' not in abstract.lower() else abstract
        keywords = self.concatenate_texts(page.intersect_by_box('keywords'))
        keywords = 'Paper Keywords: ' + keywords if 'keywords' not in keywords.lower() else keywords
        return(title, authors, abstract, keywords)

    def wrap_rows(self, first_row : Entity, sec_row : Entity) -> Tuple[Entity, Entity]:
        """wraps the first_row that ends with some_wo- and the sec_row that starts with rd."""
        first_row_words = first_row.text.split(' ')
        sec_row_words = sec_row.text.split(' ')
        wrapped_word = first_row_words[-1].replace('-', '').strip() + sec_row_words[0]
        first_row_words[-1] = wrapped_word # replace last word of first row with wrapped word
        sec_row_words.pop(0) # remove first word of second row
        first_row.text = ' '.join(first_row_words).rstrip()
        sec_row.text = ' '.join(sec_row_words).rstrip()
        return (first_row, sec_row)

    def extend_box(self, ent : Entity, amount : float) -> Entity:
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

    def check_box_intersections(self, row_box: Box, page: Entity, box_types: List[str]) -> bool:
        """Checks if row intersects with any of the specified box types in the page."""
        for box_type in box_types:
            if any([row_box.is_overlap(item.boxes[0]) for item in page.intersect_by_box(box_type)]):
                return True
        return False

    def filter_preliminary_row(self, row : Entity, page : Entity) -> bool:
        """Returns True if row intersects Titles, Abstracts, Authors and keywords from the page."""
        preliminary_types = ['titles', 'authors', 'abstracts', 'keywords']
        return self.check_box_intersections(row.boxes[0], page, preliminary_types)

    def filter_row(self, row : Entity, page : Entity) -> bool:
        """Returns True if row intersects any figure, table or equation from the page."""
        filter_types = ['figures', 'tables', 'captions', 'equations', 'footers', 'footnotes', 'headers']
        return self.check_box_intersections(row.boxes[0], page, filter_types)

    def get_section(self, doc : Document, row : Entity) -> Optional[Entity]:
        """Returns the section that intersects with the row, None Otherwise."""
        sections = doc.intersect_by_box(row, 'sections')
        return sections[0] if len(sections) > 0 else None

    def find_captions_from_image(self, image : Entity, doc : Document, entity_type : str = 'captions') -> Optional[str]:
        """Returns the entity of type entity_type that intersects with ent."""
        ext_entity = self.extend_box(image, 0.05)
        entities = doc.intersect_by_box(ext_entity, entity_type)
        if not len(entities)>0: return None
        return self.concatenate_texts(entities)

    def extract_image_from_box(self, pdf_doc : fitz.Document, fig : Entity, page : Entity, page_wdth : int, page_hght : int ) -> Image:
        """Extracts the Image from the page that intersects with the box."""
        page_num = fig.boxes[0].page
        fig_box = fig.boxes[0].to_absolute(page_wdth, page_hght).xy_coordinates
        fig_box = [el*self.zoom_factor for el in fig_box]
        mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pdf_page = pdf_doc[page_num]
        pix = pdf_page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        cropped_img = img.crop(fig_box)
        return cropped_img


    def convert_rows_to_markdown(self, doc : Document, proc_rows : List[Dict[str,str|Entity]]) -> str:
        """Converts extracted rows into markdown format."""
        content = ''
        title, authors, abstract, keywords = self.extract_paper_info(doc.pages[0])
        content += f"# {title}\n\n"
        content += f"{authors}\n\n"
        content += f"{abstract}\n\n"
        content += f"{keywords}\n"
        for row_idx, row in enumerate(proc_rows):

            row_tipe = row['type']
            row_ent = row['entity']

            if row_tipe == self.SECTION:
                content += f"\n## {row_ent.text}\n\n"

            elif row_tipe == self.PARAGRAPH:
                if self.WRAP_ROWS:
                    if row_ent.text.endswith('-'):
                        try:
                            next_row = proc_rows[row_idx + 1]['entity']
                            cur, next = self.wrap_rows(row_ent, next_row)
                            proc_rows[row_idx]['entity'] = cur # for consistency
                            proc_rows[row_idx + 1]['entity'] = next # update next row
                        except IndexError as e:
                            print(f"WRAPPING ROWS: NO NEXT ROW FOUND - {e}")
                            continue
                    # wrap "wo- \n rd" sequences in "word" 
                content += f"{row_ent.text}\n"

        self.logger.info("FINISHED CONVERTING EXTRACTED ROWS TO MARKDOWN")
        return content

    def process_document(self, document_path : str) -> Tuple[str, ImageData]:
        """Processes the document and returns the markdown content and image data."""

        recipe = CoreRecipe()
        doc = recipe.run(document_path)
        pdf_doc = fitz.open(document_path)

        ref_rows : List[Entity] = [] # content of the references section
        found_ref = False

        proc_rows : List[Dict[str,str|Entity]] = []
        image_data : ImageData = []
        width, height = doc.images[0]._pilimage.size
        for page_idx, page in enumerate(doc.pages):

            self.logger.info(f"PROCESSING PAGE {page_idx}")
            page_rows = [x for x in page.intersect_by_span('rows')]
            page_figs =  page.intersect_by_box('figures')
            self.logger.debug(f"FOUND {len(page_rows)} ROW(s) AND {len(page_figs)} FIGURE(s) IN PAGE {page_idx}")

            #extract image data from the page
            for fig_idx, fig in enumerate(page_figs):
                caption = self.find_captions_from_image(fig, doc)
                self.logger.debug(f"FOUND FIGURE {fig_idx} IN PAGE {page_idx}")
                self.logger.debug(f"FOUND CAPTION {caption}")
                img = self.extract_image_from_box(pdf_doc, fig, page, width, height)
                data = {'caption': caption, 'page_id': page_idx, 'fig_id': fig_idx}
                image_data.append((img, data))

            # extract text data from the page
            for row_idx, row in enumerate(page_rows):
                # skipping rows that belong to preliminary or additional paper sections
                if self.filter_preliminary_row(row, page) or self.filter_row(row, page):
                    continue
                # check if row belongs to a section, if so, add the section to the processed rows
                if section := self.get_section(doc, row):
                    if found_ref:
                        self.logger.info(f"FOUND NEW SECTION AFTER REFERENCES - STOPPING")
                        break
                    if section not in [entry['entity'] for entry in proc_rows if entry['type'] == self.SECTION]:
                        if any(sub in section.text.lower() for sub in ['reference', 'citation', 'bibliograph']):
                            self.logger.debug(f"FOUND REFERENCES PARAGRAPH ON PAGE {page_idx}")
                            found_ref = True
                            continue
                        self.logger.debug(f"ADDED SECTION {section.text}")
                        proc_rows.append( {'type':self.SECTION, 'entity':section} )
                    continue
                
                if found_ref:
                    ref_rows.append(row)
                else:
                    proc_rows.append( {'type': self.PARAGRAPH, 'entity':row} )

        pdf_doc.close()
        # convert processed rows into markdown format
        markdown_content = self.convert_rows_to_markdown(doc, proc_rows)
        return markdown_content, image_data