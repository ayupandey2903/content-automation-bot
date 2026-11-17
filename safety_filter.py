BANNED_WORDS = [
    "porn", "nude", "naked", "xxx", "nsfw",
    "fuck", "shit", "bitch", "asshole", "bastard",
    "kill yourself", "slur_placeholder"
    # add more words here as needed
]


def is_safe(text: str) -> bool:
    """Returns True if text passes the safety check, False if it should be blocked."""
    lowered = text.lower()
    for word in BANNED_WORDS:
        if word in lowered:
            return False
    return True