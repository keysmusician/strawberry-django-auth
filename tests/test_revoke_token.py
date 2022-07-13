from .testCases import DefaultTestCase, RelayTestCase

# GRAPHQL_JWT = {
#     "JWT_LONG_RUNNING_REFRESH_TOKEN": True,
# }


class RevokeTokenTestCaseMixin:
    def setUp(self):
        unverified_user = self.register_user(email="foo@email.com", username="foo_username")
        unverified_user.status.verified = True
        unverified_user.status.save()
        unverified_user.refresh_from_db()
        super().setUp()

    def test_revoke_token(self):
        query = self.login_query(username="foo_username")
        executed = self.make_request(query)
        self.assertTrue(executed["obtainPayload"]["refreshToken"])

        query = self.get_revoke_query(executed["obtainPayload"]["refreshToken"])
        executed = self.make_request(query)
        self.assertTrue(executed["success"])
        self.assertTrue(executed["revokePayload"]["revoked"])
        self.assertFalse(executed["errors"])

    def test_invalid_token(self):
        query = self.get_revoke_query("invalid_token")
        executed = self.make_request(query)
        self.assertFalse(executed["success"])
        self.assertTrue(executed["errors"])
        self.assertFalse(executed["revokePayload"])


class RevokeTokenTestCase(RevokeTokenTestCaseMixin, DefaultTestCase):
    def get_revoke_query(self, token):
        return """
        mutation {
        revokeToken(refreshToken: "%s" )
            {
        success
        errors
        revokePayload{
          revoked
        }
      }
    }
        """ % (
            token
        )


class VerifyTokenRelayTestCase(RevokeTokenTestCaseMixin, RelayTestCase):
    def get_revoke_query(self, token):
        return """
        mutation {
        revokeToken(input: {refreshToken: "%s"} )
           {
        success
        errors
        revokePayload{
          revoked
        }
      }
    }
        """ % (
            token
        )
