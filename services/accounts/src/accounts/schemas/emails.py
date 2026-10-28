from typing import Literal

from pydantic import BaseModel, Field, model_validator

from accounts.constants.emails import MAX_RECIPIENTS_PER_CALL, ConsentSource, EmailSetting


class EmailPreferencesOut(BaseModel):
    candidate_finished: bool
    invite_undelivered: bool
    ats_not_invited: bool
    interview_ready: bool
    reminders: bool
    updates: bool
    promotions: bool


class EmailPreferencesIn(BaseModel):
    """Only the settings to change; the rest stay as they are."""

    changes: dict[EmailSetting, bool] = Field(min_length=1)
    source: Literal[ConsentSource.SIGN_IN, ConsentSource.SETTINGS]

    @model_validator(mode="after")
    def sign_in_sets_only_marketing(self) -> "EmailPreferencesIn":
        # Signing in shows the updates opt-out and an unticked promotions box: it may set updates
        # either way, and only turn promotions on.
        if self.source == ConsentSource.SIGN_IN and any(
            setting not in (EmailSetting.UPDATES, EmailSetting.PROMOTIONS)
            or (setting == EmailSetting.PROMOTIONS and not on)
            for setting, on in self.changes.items()
        ):
            raise ValueError("Signing in may only set updates and turn on promotions.")

        return self


class UnsubscribeIn(BaseModel):
    """The settings an unsubscribe link turns off."""

    settings: list[EmailSetting] = Field(min_length=1)


class RecipientsIn(BaseModel):
    user_ids: list[str] = Field(max_length=MAX_RECIPIENTS_PER_CALL)


class RecipientOut(BaseModel):
    user_id: str
    email: str
    # The interface language, emails are written in.
    language: str
    preferences: EmailPreferencesOut


class RecipientsOut(BaseModel):
    recipients: list[RecipientOut]


class AdminEmailChangesIn(BaseModel):
    """A superadmin's changes to a user's settings; the rest stay as they are."""

    changes: dict[EmailSetting, bool] = Field(min_length=1)


class EmailAccountOut(BaseModel):
    user_id: str
    email: str
    preferences: EmailPreferencesOut


class EmailLookupOut(BaseModel):
    """The account with the address a superadmin looked up, or none."""

    account: EmailAccountOut | None


class UserIdsOut(BaseModel):
    user_ids: list[str]


class WithSettingIn(BaseModel):
    user_ids: list[str] = Field(max_length=MAX_RECIPIENTS_PER_CALL)
    setting: Literal[EmailSetting.UPDATES, EmailSetting.PROMOTIONS]
