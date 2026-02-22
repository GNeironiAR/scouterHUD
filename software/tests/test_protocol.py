"""Tests for QR-Link protocol parser."""

import pytest

from scouterhud.qrlink.protocol import DeviceLink, parse_qrlink_url


class TestParseQrlinkUrl:
    """Tests for parse_qrlink_url()."""

    def test_full_url_with_all_params(self):
        url = "qrlink://v1/monitor-bed-12/mqtt/192.168.1.10:1883?auth=pin&t=ward3/bed12/vitals"
        link = parse_qrlink_url(url)

        assert link is not None
        assert link.version == 1
        assert link.id == "monitor-bed-12"
        assert link.proto == "mqtt"
        assert link.host == "192.168.1.10"
        assert link.port == 1883
        assert link.auth == "pin"
        assert link.topic == "ward3/bed12/vitals"

    def test_minimal_url_no_query(self):
        url = "qrlink://v1/device-001/mqtt/localhost:1883"
        link = parse_qrlink_url(url)

        assert link is not None
        assert link.id == "device-001"
        assert link.auth == "open"
        assert link.topic is None

    def test_auth_only_no_topic(self):
        url = "qrlink://v1/device-001/mqtt/10.0.0.1:1883?auth=token"
        link = parse_qrlink_url(url)

        assert link is not None
        assert link.auth == "token"
        assert link.topic is None

    def test_topic_only_no_auth(self):
        url = "qrlink://v1/device-001/mqtt/10.0.0.1:1883?t=sensors/temp"
        link = parse_qrlink_url(url)

        assert link is not None
        assert link.auth == "open"
        assert link.topic == "sensors/temp"

    def test_all_supported_protos(self):
        for proto in ("mqtt", "http", "ws", "ble", "mdns"):
            url = f"qrlink://v1/dev/{ proto}/host:8080"
            link = parse_qrlink_url(url)
            assert link is not None
            assert link.proto == proto

    def test_all_supported_auth_methods(self):
        for auth in ("open", "pin", "token", "mtls", "mfa"):
            url = f"qrlink://v1/dev/mqtt/host:1883?auth={auth}"
            link = parse_qrlink_url(url)
            assert link is not None
            assert link.auth == auth

    def test_unsupported_auth_rejects_fail_closed(self):
        """Phase S0: unknown auth methods are rejected, not defaulted to open."""
        url = "qrlink://v1/dev/mqtt/host:1883?auth=foobar"
        link = parse_qrlink_url(url)
        assert link is None

    def test_url_too_long_rejected(self):
        """Phase S0: URLs exceeding max length are rejected."""
        url = "qrlink://v1/dev/mqtt/host:1883?t=" + "a" * 500
        link = parse_qrlink_url(url)
        assert link is None

    def test_unsupported_proto_returns_none(self):
        url = "qrlink://v1/dev/ftp/host:21"
        assert parse_qrlink_url(url) is None

    def test_wrong_version_returns_none(self):
        url = "qrlink://v2/dev/mqtt/host:1883"
        assert parse_qrlink_url(url) is None

    def test_invalid_version_format_returns_none(self):
        url = "qrlink://1/dev/mqtt/host:1883"
        assert parse_qrlink_url(url) is None

    def test_not_qrlink_scheme_returns_none(self):
        assert parse_qrlink_url("http://example.com") is None
        assert parse_qrlink_url("mqtt://broker:1883") is None
        assert parse_qrlink_url("") is None

    def test_too_few_segments_returns_none(self):
        assert parse_qrlink_url("qrlink://v1/dev/mqtt") is None
        assert parse_qrlink_url("qrlink://v1/dev") is None
        assert parse_qrlink_url("qrlink://v1") is None

    def test_missing_port_returns_none(self):
        url = "qrlink://v1/dev/mqtt/hostonly"
        assert parse_qrlink_url(url) is None

    def test_non_numeric_port_returns_none(self):
        url = "qrlink://v1/dev/mqtt/host:abc"
        assert parse_qrlink_url(url) is None


class TestDeviceLink:
    """Tests for DeviceLink dataclass."""

    def _make_link(self, **kwargs):
        defaults = dict(version=1, id="test-01", proto="mqtt", host="localhost", port=1883)
        defaults.update(kwargs)
        return DeviceLink(**defaults)

    def test_endpoint_property(self):
        link = self._make_link(host="10.0.0.1", port=9999)
        assert link.endpoint == "10.0.0.1:9999"

    def test_meta_topic_with_topic(self):
        link = self._make_link(topic="ward3/bed12/vitals")
        assert link.meta_topic == "ward3/bed12/vitals/$meta"

    def test_meta_topic_without_topic(self):
        link = self._make_link(topic=None)
        assert link.meta_topic is None

    def test_defaults(self):
        link = self._make_link()
        assert link.auth == "open"
        assert link.name is None
        assert link.type is None
        assert link.refresh_ms == 2000
        assert link.layout == "auto"
        assert link.schema == {}

    def test_update_from_metadata(self):
        link = self._make_link()
        meta = {
            "name": "Bed 12 Monitor",
            "type": "medical.patient_monitor",
            "icon": "heartbeat",
            "refresh_ms": 1000,
            "layout": "medical",
            "schema": {"spo2": {"alert_below": 90}},
        }
        link.update_from_metadata(meta)

        assert link.name == "Bed 12 Monitor"
        assert link.type == "medical.patient_monitor"
        assert link.icon == "heartbeat"
        assert link.refresh_ms == 1000
        assert link.layout == "medical"
        assert link.schema == {"spo2": {"alert_below": 90}}

    def test_update_from_partial_metadata(self):
        link = self._make_link()
        link.update_from_metadata({"name": "Partial"})

        assert link.name == "Partial"
        assert link.type is None  # unchanged
        assert link.refresh_ms == 2000  # unchanged

    def test_update_from_empty_metadata(self):
        link = self._make_link(name="Original")
        link.update_from_metadata({})
        assert link.name == "Original"  # unchanged
