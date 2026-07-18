from src.research.stats_client import _name_matches


def test_matches_same_club_across_sources():
    assert _name_matches("Bournemouth", "AFC Bournemouth")
    assert _name_matches("Manchester United", "Manchester United FC")
    assert _name_matches("Manchester City", "Manchester City FC")
    assert _name_matches("Brighton and Hove Albion", "Brighton & Hove Albion FC")


def test_never_matches_different_clubs():
    assert not _name_matches("Manchester United", "Manchester City FC")
    assert not _name_matches("Leeds United", "Newcastle United FC")
    assert not _name_matches("Coventry City", "Manchester City FC")
