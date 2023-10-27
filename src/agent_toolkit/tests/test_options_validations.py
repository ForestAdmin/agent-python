from unittest import TestCase

from forestadmin.agent_toolkit.options import Options, OptionValidator
from forestadmin.datasource_toolkit.exceptions import ForestException


class TestOptionValidator(TestCase):
    def test_with_default_options_should_enrich_options_with_defaults(self):
        options: Options = {}
        new_options = OptionValidator.with_defaults(options)
        self.assertEqual(new_options, {**OptionValidator.DEFAULT_OPTIONS, "instant_cache_refresh": False})

    def test_validate_options_should_raise_when_no_or_wrong_env_secret(self):
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳options\['env_secret'] is missing or invalid. You can"
            + r" retrieve its value from https:\/\/www.forestadmin.com",
            OptionValidator.validate_options,
            {},
        )
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳options\['env_secret'] is missing or invalid. You can"
            + r" retrieve its value from https:\/\/www.forestadmin.com",
            OptionValidator.validate_options,
            {"env_secret": "bla"},
        )

    def test_validate_options_should_raise_when_server_url_is_not_string(self):
        options = {
            "env_secret": "da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
            "server_url": True,
        }
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳options\['server_url'\] is missing or invalid. It should contain an URL "
            + r'\(i.e. "https:\/\/api.forestadmin.com"\)',
            OptionValidator.validate_options,
            options,
        )

    def test_validate_options_should_raise_when_server_url_is_not_http_or_invalid(self):
        options = {
            "env_secret": "da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
            "server_url": "ftp://test.com",
        }
        self.assertRaisesRegex(
            ForestException,
            r"🌳🌳🌳options\['server_url'\] is missing or invalid. It should contain an URL "
            + r'\(i.e. "https:\/\/api.forestadmin.com"\)',
            OptionValidator.validate_options,
            options,
        )

    def test_validate_options_should_raise_when_schema_path_is_not_str(self):
        options = {
            "env_secret": "da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
            "server_url": "http://test.com",
            "schema_path": True,
        }
        self.assertRaisesRegex(
            ForestException,
            r'🌳🌳🌳options\["schema_path"\] is invalid. It should contain a relative filepath '
            + r'where the schema should be loaded\/updated \(i.e. ".\/.forestadmin-schema.json"\)',
            OptionValidator.validate_options,
            options,
        )

    def test_validate_options_should_raise_when_schema_path_is_not_valid_path(self):
        options = {
            "env_secret": "da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
            "server_url": "http://test.com",
            "schema_path": "/dont_exists/",
        }
        self.assertRaisesRegex(
            ForestException,
            r'🌳🌳🌳options\["schema_path"\] is invalid. It should contain a relative filepath '
            + r'where the schema should be loaded\/updated \(i.e. ".\/.forestadmin-schema.json"\)',
            OptionValidator.validate_options,
            options,
        )

        options = {
            "env_secret": "da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
            "server_url": "http://test.com",
            "schema_path": "/dont_exists/.forestadmin-schema.json",
        }
        self.assertRaisesRegex(
            ForestException,
            r'🌳🌳🌳options\["schema_path"\] is invalid. It should contain a relative filepath '
            + r'where the schema should be loaded\/updated \(i.e. ".\/.forestadmin-schema.json"\)',
            OptionValidator.validate_options,
            options,
        )

    def test_validate_options_should_raise_when_auth_secret_is_not_set(self):
        options = {
            "env_secret": "da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
            "server_url": "http://test.com",
            "schema_path": "./.forestadmin-schema.json",
            "auth_secret": True,
        }
        self.assertRaisesRegex(
            ForestException,
            r'🌳🌳🌳options\["auth_secret"\] is invalid. Any long random string should work '
            + r'\(i.e. "OfpssLrbgF3P4vHJTTpb"\)',
            OptionValidator.validate_options,
            options,
        )

    def test_validate_options_should_raise_when_prefix_is_not_set(self):
        options = {
            "env_secret": "da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
            "server_url": "http://test.com",
            "schema_path": "./.forestadmin-schema.json",
            "auth_secret": "auth_secret",
            "prefix": False,
        }
        self.assertRaisesRegex(
            ForestException,
            r'🌳🌳🌳options\["prefix"\] is invalid. It should contain the prefix on which '
            + r'forest admin routes should be mounted \(i.e. "\/api\/v1"\)',
            OptionValidator.validate_options,
            options,
        )

    def test_validate_options_should_return_options_when_all_validations_passes(self):
        options = {
            "env_secret": "da4fc9331a68a18c2262154c74d9acb22f335724c8f2a510f8df187fa808703e",
            "server_url": "http://test.com",
            "schema_path": "./.forestadmin-schema.json",
            "auth_secret": "auth_secret",
            "prefix": "forest",
        }
        new_options = OptionValidator.validate_options(options)
        self.assertEqual(options, new_options)
