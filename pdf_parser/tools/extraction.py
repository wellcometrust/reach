import re


def _find_elements(pdf_file, keyword):
    """Return an array of elements defining section matching the given keyword.
       Built to be used only inside the grab_section() function."""

    titles = []
    titles_font_size = 0
    list_fonts = pdf_file.get_font_size_list()
    max_fonts_name = ''

    # Get the name of the biggest font
    for line in pdf_file.get_lines_by_font_size(max(list_fonts)):
        max_fonts_name = line.font_face
        break

    mean_fonts = pdf_file.get_mean_font_size()
    upper_mean = pdf_file.get_upper_mean_font_size()
    for fsize in list_fonts:
        for line in pdf_file.get_lines_by_font_size(fsize):

            # If a font is bold, in title font and bigger than other,
            # it is probably a title.
            font_is_bigger = fsize >= upper_mean + (upper_mean - mean_fonts)
            font_is_big_and_bold = font_is_bigger and line.bold
            font_is_title_like = (fsize > upper_mean + 2
                                  and line.font_face == max_fonts_name)

            if font_is_big_and_bold or font_is_title_like:
                text = line.text
                regex = r'(^|^.* +)' + keyword + 's?[ \n:]*$'
                match = re.match(regex, text, re.IGNORECASE)
                if match:
                    titles_font_size = line.size

    # Get all the line of found title font size
    titles_section = pdf_file.get_lines_by_font_size(titles_font_size)
    start_title = None
    for line in titles_section:
        if start_title:
            titles.append((start_title, line))
            start_title = None
        if keyword in line.text.lower():
            start_title = line
    if start_title:
        titles.append((start_title, None))

    return titles
