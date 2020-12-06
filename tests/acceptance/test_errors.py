"""
test / or /errors handler
"""

from .test_baseclass import TestBase


class TestError(TestBase):
    """
    Test Error page 404
    """
    def test_error_404(self):
        """
        GET /error
        WHEN user go to a non exist end point /error directory
        THEN 404 page should appear
        """
        response = self.app.get('/error', content_type='html/text')
        self.assertEqual(
            response.status_code,
            404,
            "cannot catch 404 error"
        )






