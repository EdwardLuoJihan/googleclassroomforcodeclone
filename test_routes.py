import unittest
from app import app, db
from app.models import User, Class, Assignment, Submission

class BasicTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_registration(self):
        response = self.app.post('/register', data=dict(
            username='testuser',
            email='test@example.com',
            password='password',
            class_code='12345'
        ), follow_redirects=True)
        self.assertIn(b'Your account has been created!', response.data)

    def test_submission(self):
        # Add logic to test assignment submission
        pass

    def test_grading(self):
        # Add logic to test assignment grading
        pass

if __name__ == '__main__':
    unittest.main()
