"""A campaign's audience, read a page at a time in id order."""

import uuid

from library.constants.emails import ConsentSource, EmailSetting
from library.repositories import emails


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


def test_of_some_users_those_with_a_setting_on_are_kept_in_order(run):
    tag = uuid.uuid4().hex[:8]
    on, off, never = f"{tag}-on", f"{tag}-off", f"{tag}-never"

    async def scenario():
        await emails.change(on, {EmailSetting.UPDATES: True}, ConsentSource.SETTINGS)
        await emails.change(off, {EmailSetting.UPDATES: True}, ConsentSource.SETTINGS)
        await emails.change(off, {EmailSetting.UPDATES: False}, ConsentSource.SETTINGS)

        return await emails.having(EmailSetting.UPDATES, [never, off, on])

    assert run(scenario()) == [on]
