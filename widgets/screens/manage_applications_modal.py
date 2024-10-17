from textual.screen import Screen
from textual.containers import Container, Horizontal
from textual.widgets import Static, Button, TextArea
from textual.message import Message
from theme import conda_theme

class ManageApplicationsModal(Screen):
    class ApplicationsUpdated(Message):
        """Sent when applications are updated."""

    def compose(self):
        yield Container(
            Static("Manage Applications", classes="modal-title"),
            TextArea(id="yaml_editor", language="yaml"),
            Horizontal(
                Button("Save", id="save_button", variant="primary"),
                Button("Cancel", id="cancel_button", variant="error"),
                classes="button-container"
            ),
            id="manage_applications_modal"
        )

    def on_mount(self):
        yaml_editor = self.query_one("#yaml_editor", TextArea)
        yaml_editor.register_theme(conda_theme)
        yaml_editor.theme = "conda"
        yaml_editor.show_line_numbers = True
        
        with open("applications.yaml", "r") as file:
            yaml_content = file.read()
        
        yaml_editor.load_text(yaml_content)
        yaml_editor.border_title = "applications.yaml"

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "save_button":
            self.save_yaml()
        self.app.pop_screen()

    def save_yaml(self):
        yaml_editor = self.query_one("#yaml_editor", TextArea)
        updated_content = yaml_editor.text
        with open("applications.yaml", "r") as file:
            original_content = file.read()
        if updated_content != original_content:
            with open("applications.yaml", "w") as file:
                file.write(updated_content)
            self.post_message(self.ApplicationsUpdated())
