import unittest

from utils import split_sections, process_reference_section
from main import SectionedDocument

class TestSplit(unittest.TestCase):
	
	def test_empty_sections(self):
		references = split_sections("")
		self.assertEqual(references, [], "Should be []")

	def test_oneline_section(self):
		references = split_sections("This is one line")
		self.assertEqual(references, ["This is one line"], "Should be ['This is one line']")

	def test_empty_lines_section(self):
		references = split_sections("\n\n\n")
		self.assertEqual(references, [], "Should be []")

	def test_normal_section(self):
		references = split_sections("One reference\nTwo references\nThree references\n")
		self.assertEqual(references, ["One reference", "Two references", "Three references"],
			"Should be ['One reference', 'Two reference', 'Three reference']")

class TestProcessReferenceSection(unittest.TestCase):

	def test_no_section_in_document(self):
		doc = SectionedDocument(
			None,
			'uri',
			'id'
		)
		with self.assertRaises(TypeError):
			process_reference_section(doc, '\n')
