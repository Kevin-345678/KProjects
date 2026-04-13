import importlib
import sys
import types
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


def load_monitor():
    dns_module = types.ModuleType("dns")
    dns_module.resolver = types.ModuleType("dns.resolver")

    google_module = types.ModuleType("google")
    oauth2_module = types.ModuleType("google.oauth2")
    credentials_module = types.ModuleType("google.oauth2.credentials")
    credentials_module.Credentials = object

    googleapiclient_module = types.ModuleType("googleapiclient")
    discovery_module = types.ModuleType("googleapiclient.discovery")
    discovery_module.build = lambda *args, **kwargs: object()

    with patch.dict(
        sys.modules,
        {
            "dns": dns_module,
            "dns.resolver": dns_module.resolver,
            "google": google_module,
            "google.oauth2": oauth2_module,
            "google.oauth2.credentials": credentials_module,
            "googleapiclient": googleapiclient_module,
            "googleapiclient.discovery": discovery_module,
        },
    ):
        sys.modules.pop("monitor", None)
        return importlib.import_module("monitor")


class MonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.monitor = load_monitor()

    def test_parse_list_trims_empty_values(self):
        self.assertEqual(
            self.monitor.parse_list(" example.com, ,example.org "),
            ["example.com", "example.org"],
        )

    def test_parse_gcs_uri_requires_bucket_and_object(self):
        self.assertEqual(
            self.monitor.parse_gcs_uri("gs://bucket/path/state.json"),
            ("bucket", "path/state.json"),
        )

        with self.assertRaisesRegex(RuntimeError, "must start with gs://"):
            self.monitor.parse_gcs_uri("bucket/path/state.json")

        with self.assertRaisesRegex(RuntimeError, "bucket and object path"):
            self.monitor.parse_gcs_uri("gs://bucket")

    def test_local_state_round_trip(self):
        with TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.json"
            with patch.dict(
                "os.environ",
                {
                    "POSTMASTER_STATE_PATH": str(state_path),
                    "POSTMASTER_STATE_GCS_URI": "",
                },
                clear=False,
            ):
                self.assertEqual(self.monitor.load_state(), {})
                self.monitor.save_state({"example.com": {"domain_reputation": "HIGH"}})
                self.assertEqual(
                    self.monitor.load_state(),
                    {"example.com": {"domain_reputation": "HIGH"}},
                )

    def test_configured_domains_reads_txt_file(self):
        with TemporaryDirectory() as tmp_dir:
            domains_path = Path(tmp_dir) / "domains.txt"
            domains_path.write_text("# comment\nexample.com\n\nexample.org\n")

            with patch.dict(
                "os.environ",
                {
                    "POSTMASTER_DOMAINS": "",
                    "POSTMASTER_DOMAINS_FILE": str(domains_path),
                },
                clear=False,
            ):
                self.assertEqual(
                    self.monitor.configured_domains(),
                    ["example.com", "example.org"],
                )

    def test_configured_dkim_selectors_reads_txt_file(self):
        with TemporaryDirectory() as tmp_dir:
            selectors_path = Path(tmp_dir) / "dkim_selectors.txt"
            selectors_path.write_text("nce2048\nnc2048\ninb\n")

            with patch.dict(
                "os.environ",
                {
                    "POSTMASTER_DKIM_SELECTORS": "",
                    "POSTMASTER_DKIM_SELECTORS_FILE": str(selectors_path),
                },
                clear=False,
            ):
                self.assertEqual(
                    self.monitor.configured_dkim_selectors(),
                    ["nce2048", "nc2048", "inb"],
                )

    def test_configured_ips_reads_txt_file(self):
        with TemporaryDirectory() as tmp_dir:
            ips_path = Path(tmp_dir) / "ips.txt"
            ips_path.write_text("# comment\n80.91.87.73\n194.104.130.31\n")

            with patch.dict(
                "os.environ",
                {
                    "POSTMASTER_IPS": "",
                    "POSTMASTER_IPS_FILE": str(ips_path),
                },
                clear=False,
            ):
                self.assertEqual(
                    self.monitor.configured_ips(),
                    ["80.91.87.73", "194.104.130.31"],
                )

    def test_extract_monitored_ip_reputations_matches_sample_ips(self):
        stat = {
            "ipReputations": [
                {"reputation": "HIGH", "sampleIps": ["80.91.87.73", "10.0.0.1"]},
                {"reputation": "LOW", "sampleIps": ["194.104.130.31"]},
            ]
        }

        self.assertEqual(
            self.monitor.extract_monitored_ip_reputations(
                stat,
                ["80.91.87.73", "194.104.130.31", "194.104.130.32"],
            ),
            [
                {"ip": "80.91.87.73", "reputation": "HIGH"},
                {"ip": "194.104.130.31", "reputation": "LOW"},
            ],
        )

    def test_render_email_escapes_domain_content(self):
        html = self.monitor.render_email(
            "2026-04-13",
            {
                "bad<domain>.com": {
                    "latest_date": "2026-04-12",
                    "domain_reputation": "HIGH",
                    "previous_domain_reputation": "MEDIUM",
                    "ip_reputation": "HIGH: 1",
                    "previous_ip_reputation": "MEDIUM: 1",
                    "spf_status": "OK",
                    "spf_detail": "v=spf1 include:example.com -all",
                    "dkim_status": "OK",
                    "dkim_detail": "Selector default found",
                    "dmarc_status": "OK",
                    "dmarc_detail": "v=DMARC1; p=none",
                    "alerts": ["Domain reputation improved from MEDIUM to HIGH"],
                }
            },
        )

        self.assertIn("bad&lt;domain&gt;.com", html)
        self.assertIn("Domain reputation improved", html)
        self.assertNotIn("bad<domain>.com", html)


if __name__ == "__main__":
    unittest.main()
