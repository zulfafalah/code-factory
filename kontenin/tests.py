import pytest

from kontenin.services import _extract_aweme_list, parse_aweme

AWEME_FIXTURE = {
    "aweme_id": "7300000000000000000",
    "desc": "Cara menanam cabai di polybag",
    "share_url": "https://www.tiktok.com/@petanimuda/video/7300000000000000000",
    "video": {
        "duration": 95000,
        "cover": {"url_list": ["https://cdn.example/cover.jpg"]},
    },
    "author": {"nickname": "Petani Muda", "unique_id": "petanimuda"},
    "statistics": {
        "play_count": 12000,
        "digg_count": 800,
        "comment_count": 40,
        "share_count": 12,
    },
}


class TestParseAweme:
    def test_maps_the_fields_kontenin_needs(self):
        fields = parse_aweme(AWEME_FIXTURE)

        assert fields["external_video_id"] == "7300000000000000000"
        assert fields["author_unique_id"] == "petanimuda"
        assert fields["cover_url"] == "https://cdn.example/cover.jpg"
        assert fields["like_count"] == 800

    def test_converts_duration_from_milliseconds(self):
        # TikTok reports milliseconds; the duration limit is expressed in seconds.
        assert parse_aweme(AWEME_FIXTURE)["duration_seconds"] == 95

    def test_builds_a_share_url_when_the_api_omits_one(self):
        item = {**AWEME_FIXTURE}
        del item["share_url"]

        assert parse_aweme(item)["video_url"] == (
            "https://www.tiktok.com/@petanimuda/video/7300000000000000000"
        )

    def test_survives_a_result_with_nothing_in_it(self):
        fields = parse_aweme({})

        assert fields["external_video_id"] == ""
        assert fields["duration_seconds"] == 0


class TestExtractAwemeList:
    @pytest.mark.parametrize(
        "payload",
        [
            {"data": {"aweme_list": [1, 2]}},
            {"data": {"data": [1, 2]}},
            {"data": [1, 2]},
            {"aweme_list": [1, 2]},
        ],
    )
    def test_finds_the_list_across_known_response_shapes(self, payload):
        assert _extract_aweme_list(payload) == [1, 2]

    @pytest.mark.parametrize("payload", [{}, {"data": {}}, None, "nope"])
    def test_returns_empty_when_there_is_no_list(self, payload):
        assert _extract_aweme_list(payload) == []


@pytest.mark.django_db
class TestReadyPool:
    """Approval and readiness are separate - see ADR 0001."""

    def _candidate(self, **overrides):
        from kontenin.models import ContentCandidate, Topic

        topic = Topic.objects.create(name="Pertanian", keyword="pertanian")
        fields = {
            "topic": topic,
            "external_video_id": "7300000000000000000",
            "video_url": "https://www.tiktok.com/@petanimuda/video/7300000000000000000",
        }
        fields.update(overrides)
        return ContentCandidate.objects.create(**fields)

    def test_approved_without_a_file_is_not_in_the_ready_pool(self):
        from kontenin.models import ContentCandidate

        candidate = self._candidate(status=ContentCandidate.STATUS_APPROVED)

        assert candidate.is_in_ready_pool is False

    def test_ready_status_without_a_file_is_still_not_in_the_ready_pool(self):
        from kontenin.models import ContentCandidate

        candidate = self._candidate(status=ContentCandidate.STATUS_READY)

        assert candidate.is_in_ready_pool is False

    def test_a_video_is_never_offered_twice(self):
        from django.db import IntegrityError

        self._candidate()

        with pytest.raises(IntegrityError):
            self._candidate()


class TestNormalizeMsisdn:
    """The send routes accept a wrong-but-well-formed number without complaint."""

    def test_converts_a_local_leading_zero_to_the_country_code(self):
        from kontenin.services import normalize_msisdn

        assert normalize_msisdn("081578258854") == "6281578258854"

    def test_leaves_an_already_international_number_alone(self):
        from kontenin.services import normalize_msisdn

        assert normalize_msisdn("6281578258854") == "6281578258854"

    def test_strips_separators(self):
        from kontenin.services import normalize_msisdn

        assert normalize_msisdn("+62 815-7825-8854") == "6281578258854"


@pytest.mark.django_db
class TestDurationLimit:
    """Long videos are allowed; the limit is opt-in per Topic."""

    LONG_VIDEO = {**AWEME_FIXTURE, "video": {**AWEME_FIXTURE["video"], "duration": 600000}}

    def _scrape(self, monkeypatch, max_duration_seconds):
        from kontenin import services
        from kontenin.models import Topic

        topic = Topic.objects.create(
            name="Pengajian",
            keyword="pengajian islam",
            max_duration_seconds=max_duration_seconds,
        )
        monkeypatch.setattr(services, "search_videos", lambda t: [self.LONG_VIDEO])
        return services.scrape_topic(topic)

    def test_a_ten_minute_video_becomes_a_candidate_when_the_limit_is_off(self, monkeypatch):
        stats = self._scrape(monkeypatch, max_duration_seconds=0)

        assert stats["created"] == 1
        assert stats["too_long"] == 0

    def test_the_limit_still_applies_when_a_topic_sets_one(self, monkeypatch):
        stats = self._scrape(monkeypatch, max_duration_seconds=180)

        assert stats["created"] == 0
        assert stats["too_long"] == 1

    def test_a_video_exactly_at_the_limit_is_kept(self, monkeypatch):
        stats = self._scrape(monkeypatch, max_duration_seconds=600)

        assert stats["created"] == 1
