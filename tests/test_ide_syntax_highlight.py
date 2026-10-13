from pynix_gui.ide_syntax_highlight import highlight_line, highlight_document

def test_keywords_strings_numbers_and_comments():
    tokens = highlight_line('function main() // comment')
    assert [(t.kind,t.text) for t in tokens if t.kind!='plain'] == [
        ('keyword','function'),('comment','// comment')]
    tokens = highlight_line('return "hello" + 42')
    assert [(t.kind,t.text) for t in tokens if t.kind!='plain'] == [
        ('keyword','return'),('string','"hello"'),('number','42')]

def test_source_content_is_lossless():
    for line in ('', 'print("<script>") # safe', '   x = 4.2', 'foo_bar // comment'):
        assert ''.join(t.text for t in highlight_line(line)) == line

def test_multiline_document():
    data = highlight_document('function main()\n  return true')
    assert len(data) == 2
    assert any(t['kind']=='keyword' for t in data[1])

def test_editor_uses_safe_text_content():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    src = (root/'pynix_gui'/'ide_workspace_preview.py').read_text()
    assert 'highlight_document(doc.text)' in src
    assert "span.textContent=token.text" in src
    assert 'if(current===payload.source){' in src
    assert 'renderCode(file);updateEditingView();' in src
