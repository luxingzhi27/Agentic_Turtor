from app.services.examples import get_demo_page, get_example_bundle, list_examples


def test_example_bundles_include_text_file_and_link() -> None:
    for example in list_examples():
        bundle = get_example_bundle(example.example_id)

        assert "http://127.0.0.1:8000/api/demo-pages/" in bundle.content
        assert bundle.file_name.endswith("_upload.md")
        assert len(bundle.file_content) > 300


def test_demo_pages_are_available() -> None:
    for example in list_examples():
        response = get_demo_page(example.example_id)
        body = response.body.decode("utf-8")

        assert "<html" in body
        assert "</html>" in body
