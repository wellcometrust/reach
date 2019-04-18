import re
import attr
import json
import math
import ahocorasick


@attr.s
class PdfLine(object):
    """Represent a line of text from a pdf file, defined by the following
    attributes:
        - (int)size         : The font size of the line.
        - (boolean)bold     : True if the font is bold, else False.
        - (str)text         : The text of the line.
        - (int)page_number  : The page number of the line.
        - (str)font_face    : The font used for this line in the pdf file.
    """
    size = attr.ib(default=0, type=int)
    bold = attr.ib(default=False, type=bool)
    text = attr.ib(default='', type=str)
    page_number = attr.ib(default=0, type=int)
    font_face = attr.ib(default='', type=str)


@attr.s
class PdfPage(object):
    """Represent a page of text from a pdf file, defined by the following
    attributes:
        - (PdfLine[])lines    : An ordered list of all the text lines from
                                the page.
        - (int)number         : The page number.
    """
    lines = attr.ib(default=[], type=list)
    number = attr.ib(default=0, type=int)

    def display_page(self):
        """Print the content of the whole page."""
        for line in self.lines:
            print(line.text)

    def get_page_text(self, ignore_page_numbers=False):
        """Return a string containing the content of the page. If the argument
        ignore_page_number is True, try to ignore page number when it
        is possible.
        """
        if ignore_page_numbers:
            result = list(filter(lambda x: not x.text.isdigit(), self.lines))
            return '\n'.join(list(map(lambda x: x.text, result)))
        else:
            return '\n'.join(list(map(lambda x: x.text, self.lines)))


@attr.s
class PdfFile(object):
    """Represent a pdf file, defined by the following attributes:
        - (PdfPage[])pages    : An ordered list of all the pages from the pdf.
        - (boolean)has_bold   : True if the pdf has at least one bold line,
                                else False. Used to identify titles.
    """
    pages = attr.ib(default=[], type=list)
    has_bold = attr.ib(default=False, type=bool)

    def from_json(self, json_pdf):
        """Initialize a PdfFile object from a json representation."""
        dict_pdf = json.loads(json_pdf)
        pdf_pages = []
        for page in dict_pdf.get('pages', []):
            page_lines = []
            for line in page.get('lines', []):
                pdf_line = PdfLine(**line)
                page_lines.append(pdf_line)
            pdf_page = PdfPage(
                page_lines,
                page.get('number', 0)
            )
            pdf_pages.append(pdf_page)
        self.pages = pdf_pages
        self.has_bold = dict_pdf.get('has_bold', False)

    def to_json(self):
        """Return a dictionary representation of the PdfFile."""
        json_pdf_file = json.dumps(attr.asdict(self))
        return json_pdf_file

    def add_page(self, pdf_page):
        """Add a PdfPage to the pages list."""
        self.pages.append(pdf_page)

    def get_page(self, page_number):
        """Return the PdfPage for the argument (int)page_number."""
        return self.pages[page_number]

    def get_mean_font_size(self):
        """Return the mean of the pdf file font sizes."""
        sum_size = 0
        total_fonts = 0
        for page in self.pages:
            for line in page.lines:
                sum_size += line.size
                total_fonts += 1
        return math.ceil(sum_size / max(total_fonts, 1))

    def get_upper_mean_font_size(self):
        """Return the mean of all fonts ubove the average size."""
        basic_mean = self.get_mean_font_size()
        sum_size = 0
        total_fonts = 0
        for page in self.pages:
            for line in page.lines:
                if line.size > basic_mean:
                    sum_size += line.size
                    total_fonts += 1
        return int(sum_size / max(total_fonts, 1))

    def get_lines_by_font_size(self, font_size):
        """Return all the lines of (int)font_size size."""
        lines_results = []
        for page in self.pages:
            lines = [line for line in page.lines if line.size == font_size]
            lines = list(filter(lambda x: x.size == font_size, page.lines))
            lines_results.extend(lines)

        return lines_results

    def get_font_size_list(self):
        """Return a list containing all the font sizes in the pdf file."""
        font_sizes = []
        for page in self.pages:
            lines = [line.size for line in page.lines]
            font_sizes.extend(list(lines))
        # Convert to set and back to list to remove duplicates
        return list(set(font_sizes))

    def get_bold_lines(self):
        """Return all the bold lines in the document."""
        lines_results = []
        for page in self.pages:
            # lines = [line for line in page.lines if line.bold]
            lines = list(filter(lambda x: x.bold, page.lines))
            lines_results.extend(lines)

        return lines_results

    def _keyword_is_in_line(self, line, pattern):
        return pattern.search(line)

    def get_lines_by_keyword(self, keyword, context=0):
        """Return a list of lines containing (string)keyword."""
        lines_results = []
        pattern = re.compile(''.join([
            r'(^|\W)',
            keyword,
            r'(\W|$)'
        ]))
        if context > 0:
            for page in self.pages:
                lines = []
                for num, line in enumerate(page.lines):
                    if self._keyword_is_in_line(line.text, pattern):
                        first_line = max(0, num - context)
                        last_line = min(len(page.lines), num + context + 1)
                        lines = page.lines[first_line:last_line]
                lines_results.extend(list(map(lambda x: x.text, lines)))
        else:
            for page in self.pages:
                lines = list(filter(
                    lambda x: self._keyword_is_in_line(
                        x.text,
                        pattern
                    ),
                    page.lines
                ))
                lines_results.extend([line.text for line in lines])

        return lines_results

    def get_lines_by_keywords(self, keywords, context=0):
        """Return a dictionary of lines containing one of the keyboards array,
        ordered by keyword.
        """

        ac_automaton = ahocorasick.Automaton()
        keyword_dict = {}
        for index, keyword in enumerate(set(keywords)):
            ac_automaton.add_word(keyword, (index, keyword))

        lines = []
        for page in self.pages:
            lines.extend(page.lines)
        ac_automaton.make_automaton()
        for num, line in enumerate(lines):
            for index, value in ac_automaton.iter(line.text.lower()):
                pattern = re.compile(''.join([
                    r'(^|\W)',
                    value[1],
                    r'(\W|$)'
                ]), re.IGNORECASE)
                if self._keyword_is_in_line(line.text, pattern):
                    first_line = max(0, num - context)
                    last_line = min(len(lines), num + context + 1)
                    result = lines[first_line:last_line]
                    if value[1] in keyword_dict.keys():
                        keyword_dict[value[1]].extend(
                            list(map(lambda x: x.text, result))
                        )
                    else:
                        keyword_dict[value[1]] = list(
                            map(lambda x: x.text, result)
                        )
        return keyword_dict
