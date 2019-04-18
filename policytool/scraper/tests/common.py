import os.path


def get_path(p):
    return os.path.join(
        os.path.dirname(__file__),
        p
    )

TEST_PDF = get_path('pdfs/test_pdf.pdf')
