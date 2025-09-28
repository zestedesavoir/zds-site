from haystack.utils import Highlighter

MAX_WRAP_TEXT = 50


class SearchHighlighter(Highlighter):
    def render_html(self, highlight_locations=None, start_offset=None, end_offset=None):
        if start_offset is not None:
            start_offset = max([0, start_offset - MAX_WRAP_TEXT])
        if end_offset is not None:
            end_offset = min([len(self.text_block), end_offset + MAX_WRAP_TEXT])

        return super().render_html(
            highlight_locations=highlight_locations, start_offset=start_offset, end_offset=end_offset
        )
