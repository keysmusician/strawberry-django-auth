from .testCases import DefaultTestCase


class QueryTestCase(DefaultTestCase):
    def setUp(self):
        unverified_user = self.register_user(email="foo@email.com", username="foo", verified=False)
        self.user2 = self.register_user(email="bar@email.com", username="bar", verified=True)
        self.user3 = self.register_user(
            email="gaa@email.com", username="gaa", verified=True, archived=True
        )
        super().setUp()

    def test_me_authenticated(self):
        query = """
        query {
            me {
                username
            }
        }
        """
        executed = self.make_request(query, variables={"user": self.user2})
        self.assertTrue(executed["username"])

    def test_me_anonymous(self):
        query = """
        query {
            me {
                username
            }
        }
        """
        executed = self.make_request(query)
        self.assertIsNone(executed)

    def test_public_user_query(self):
        query = """
        query {
            publicUser {
                verified
            }
        }
        """
        executed = self.make_request(query, variables={"user": unverified_user})
        self.assertEqual(executed, {"verified": False})
