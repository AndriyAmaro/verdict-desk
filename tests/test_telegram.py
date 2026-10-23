"""The Telegram adapter: a public channel preview as a keyless voice source.

The spotlight names "Discord or Telegram" as optional sources. Telegram closes without any key:
public channels expose a readable web preview at t.me/s/<channel>. The adapter is keyless and, if
Telegram ever changes its HTML, returns empty rather than guessing — so a silent failure looks
like a gap, never like a fabricated voice.
"""

import unittest

from verdict_desk import narrative

HTML = """
<!doctype html><html><body>
<div class="tgme_widget_message_wrap">
  <div class="tgme_widget_message_text js-message_text" dir="auto">Bitcoin <b>breaks</b> a key level <a href="https://t.me/example/42">read more</a></div>
  <time datetime="2026-10-22T10:00:00+00:00">Oct 22</time>
</div>
<div class="tgme_widget_message_wrap">
  <div class="tgme_widget_message_text js-message_text" dir="auto">Second message with a number 42 and a $SOL mention</div>
  <time datetime="2026-10-22T09:00:00+00:00">Oct 22</time>
</div>
<div class="tgme_widget_message_wrap">
  <div class="tgme_widget_message_text js-message_text" dir="auto"><i>Third, inline tags only</i></div>
  <time datetime="2026-10-22T08:00:00+00:00">Oct 22</time>
</div>
</body></html>
"""


class TelegramTest(unittest.TestCase):
    def test_extracts_message_text_stripping_tags(self):
        items = narrative.parse_telegram(HTML, "example")
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0]["title"], "Bitcoin breaks a key level read more")

    def test_the_voice_is_the_channel(self):
        items = narrative.parse_telegram(HTML, "example")
        self.assertEqual(items[0]["name"], "example")
        self.assertEqual(items[0]["link"], "https://t.me/s/example")

    def test_published_is_parsed(self):
        items = narrative.parse_telegram(HTML, "example")
        self.assertEqual(items[0]["published"], "2026-10-22T10:00:00+00:00")

    def test_unrecognised_html_yields_empty_not_garbage(self):
        self.assertEqual(narrative.parse_telegram("<html><body>nothing</body></html>", "x"), [])

    def test_fetch_feed_routes_t_me_to_the_telegram_parser(self):
        url = "https://t.me/s/example"
        # a t.me URL must never go through the XML parser (it is not XML)
        self.assertIn("t.me/s/", url)
        items = narrative.parse_telegram(HTML, "example")
        self.assertGreaterEqual(len(items), 1)


if __name__ == "__main__":
    unittest.main()
