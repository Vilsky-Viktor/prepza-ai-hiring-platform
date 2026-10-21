"""A campaign's audience, read a page at a time in id order."""

import uuid

from app.constants.emails import ConsentSource, EmailSetting
from app.storage import emails


def test_the_users_with_a_setting_on_come_a_page_at_a_time(run):
    tag = uuid.uuid4().hex[:8]
    users = [f"{tag}-{n}" for n in range(3)]

    async def scenario():
        for user_id in users:
            await emails.change(user_id, {EmailSetting.PROMOTIONS: True}, ConsentSource.SETTINGS)

        first = await emails.ids_with(EmailSetting.PROMOTIONS, f"{tag}-", 2)
        second = await emails.ids_with(EmailSetting.PROMOTIONS, first[-1], 2)

        return first, second

    first, second = run(scenario())

    assert first == users[:2]
    assert second[0] == users[2]
