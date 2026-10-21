from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceSettings(BaseSettings):
    """What every API service reads about sign-in. Each service's Settings adds its own."""

    # A refused setting's error names the setting, never the values given: they include keys
    # and secrets, and the error goes to the start-up log.
    model_config = SettingsConfigDict(hide_input_in_errors=True)

    firebase_project_id: str
    firebase_auth_emulator_host: str = ""

    @model_validator(mode="after")
    def emulator_only_for_demo_projects(self) -> "ServiceSettings":
        # With the emulator host set, firebase_admin accepts unsigned tokens.
        if self.firebase_auth_emulator_host and not self.firebase_project_id.startswith("demo-"):
            raise ValueError("FIREBASE_AUTH_EMULATOR_HOST is only allowed for a demo- project")

        return self
