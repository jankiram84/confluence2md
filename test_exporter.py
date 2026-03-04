import unittest
from confluence_md_exporter import sanitize_name, preprocess_confluence_macros

class TestConfluenceExporter(unittest.TestCase):

    def test_sanitize_name(self):
        # Tests that illegal characters are removed
        self.assertEqual(sanitize_name("Project/Plan?"), "Project-Plan")
        self.assertEqual(sanitize_name("Hello World"), "Hello-World")

    def test_macro_conversion(self):
        # Tests that Confluence panels become blockquotes
        html = '<div class="confluence-information-macro confluence-information-macro-note"><div class="confluence-information-macro-body"><p>Test Note</p></div></div>'
        result = preprocess_confluence_macros(html)
        self.assertIn("<blockquote>", result)
        self.assertIn("<strong>Note:</strong>", result)

if __name__ == '__main__':
    unittest.main()