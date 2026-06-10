from scripts.gen_sync import GENERATED_PAIRS, REPO_ROOT, generate_formatted_source


def test_generated_sync_files_match_async_sources() -> None:
    stale_files: list[str] = []

    for pair in GENERATED_PAIRS:
        expected = generate_formatted_source(pair)
        actual = (REPO_ROOT / pair.target).read_text()
        if actual != expected:
            stale_files.append(pair.target.as_posix())

    assert not stale_files, "Generated sync files are stale: " + ", ".join(stale_files)
