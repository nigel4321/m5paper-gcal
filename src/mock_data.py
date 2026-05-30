# Static event fixtures — used in Phase 2 before real calendar integration

MOCK_EVENTS = [
    {
        "title": "Team standup",
        "start": "2026-05-30T09:00:00",
        "end": "2026-05-30T09:30:00",
        "location": "Google Meet",
        "all_day": False,
    },
    {
        "title": "Design review",
        "start": "2026-05-30T11:00:00",
        "end": "2026-05-30T12:00:00",
        "location": "Conference Room B",
        "all_day": False,
    },
    {
        "title": "Bank holiday",
        "start": "2026-05-31",
        "end": "2026-05-31",
        "location": "",
        "all_day": True,
    },
    {
        "title": "1:1 with Alice",
        "start": "2026-05-31T10:00:00",
        "end": "2026-05-31T10:45:00",
        "location": "",
        "all_day": False,
    },
    {
        "title": "A very long event title that should be truncated on the display",
        "start": "2026-06-01T14:00:00",
        "end": "2026-06-01T15:00:00",
        "location": "Some very long location name",
        "all_day": False,
    },
]
