from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Static, ListView, ListItem, Header, Footer, TextArea
from textual.reactive import reactive
from textual.binding import Binding
from textual.message import Message
import subprocess
import os
import yaml
import psutil
import sys
import threading
import traceback
import queue

from widgets.screens import ProcessesModal, ManageApplicationsModal

class CondaLauncher(App):
    CSS_PATH = "styles.tcss"

    BINDINGS = [
        Binding("ctrl+o", "show_processes", "Show Running Processes"),
        Binding("ctrl+q", "quit", "Quit")
    ]

    applications = reactive([])
    selected_app = reactive(None)
    running_processes = reactive({})
    process_outputs = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Horizontal(
                Vertical(
                    Static("Applications", classes="section-title"),
                    ListView(id="app_list"),
                    Button("Manage Applications", id="manage_applications_button"),
                    id="left-panel"
                ),
                Vertical(
                    Static("Application Details", classes="section-title"),
                    Static(id="details", classes="details-content"),
                    Horizontal(
                        Button("Launch", id="launch_button"),
                        Button("Refresh Applications", id="refresh_button"),
                        classes="button-container"
                    ),
                    id="right-panel"
                ),
                id="main-content"
            ),
            id="app-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        self.load_applications()

    def load_applications(self) -> None:
        with open("applications.yaml", "r") as file:
            data = yaml.safe_load(file)
        self.applications = data["applications"]
        app_list = self.query_one("#app_list", ListView)
        app_list.clear()
        for app in self.applications:
            app_list.append(ListItem(Static(app["name"]), name=app["name"]))

    def get_running_apps(self):
        running_apps = []
        to_remove = []
        for app_name, pid in self.running_processes.items():
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    running_apps.append((app_name, pid))
                else:
                    to_remove.append(app_name)
            except psutil.NoSuchProcess:
                to_remove.append(app_name)
        
        # Remove non-existent processes outside the loop
        for app_name in to_remove:
            del self.running_processes[app_name]
            if app_name in self.process_outputs:
                del self.process_outputs[app_name]
        
        return running_apps

    def get_app_pid(self, path):
        script_name = os.path.basename(path)
        for process in psutil.process_iter(['name', 'cmdline', 'pid']):
            try:
                if process.name().lower() == 'python.exe':
                    cmdline = process.cmdline()
                    if len(cmdline) > 1 and script_name in cmdline[-1]:
                        return process.pid
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return None

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id == "app_list":
            selected_name = event.item.name
            self.selected_app = next((app for app in self.applications if app["name"] == selected_name), None)
            if self.selected_app:
                details = f"Name: {self.selected_app['name']}\n"
                details += f"Conda Env: {self.selected_app['conda_env']}\n"
                details += f"Path: {self.selected_app['path']}\n"
                details += f"Description: {self.selected_app['description']}"
                self.query_one("#details", Static).update(details)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "launch_button":
            self.launch_application()
        elif event.button.id == "refresh_button":
            self.load_applications()
        elif event.button.id == "manage_applications_button":
            self.push_screen(ManageApplicationsModal())

    def launch_application(self) -> None:
        if not self.selected_app:
            self.notify("Please select an application.")
            return

        activate_cmd = f'conda activate {self.selected_app["conda_env"]}'
        python_cmd = f'python "{self.selected_app["path"]}"'
        full_cmd = f'{activate_cmd} && {python_cmd}'

        try:
            thread = threading.Thread(target=self._run_app_in_thread, args=(full_cmd,))
            thread.start()
            self.notify(f"Launched {self.selected_app['name']} in {self.selected_app['conda_env']} environment.")
        except Exception as e:
            self.notify(f"Error launching application: {str(e)}")
            traceback.print_exc()

    def _run_app_in_thread(self, cmd):
        print(f"Running command: {cmd}")  # Debug print
        if os.name == 'nt':  # Windows
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
        else:  # Unix-like systems
            process = subprocess.Popen(['bash', '-c', cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)

        self.running_processes[self.selected_app['name']] = process.pid
        print(f"Added process to running_processes: {self.selected_app['name']} (PID: {process.pid})")  # Debug print
        
        self.process_outputs[self.selected_app['name']] = ""

        def enqueue_output(out, app_name):
            print("Starting to read output")  # Debug print
            for line in iter(out.readline, ''):
                print(f"Read line: {line}")  # Debug print
                self.process_outputs[app_name] += line
                self.post_message(self.ProcessOutputUpdated(app_name))
            print("Finished reading output")  # Debug print
            out.close()

        threading.Thread(target=enqueue_output, args=(process.stdout, self.selected_app['name']), daemon=True).start()
        threading.Thread(target=enqueue_output, args=(process.stderr, self.selected_app['name']), daemon=True).start()

        process.wait()
        
        # Check if the process has exited normally
        if process.returncode is not None:
            if self.selected_app['name'] in self.running_processes:
                del self.running_processes[self.selected_app['name']]
            print(f"Removed process from running_processes: {self.selected_app['name']}")  # Debug print

    def get_process_output(self, app_name):
        return self.process_outputs.get(app_name, "No output available.")

    class ProcessOutputUpdated(Message):
        def __init__(self, app_name: str) -> None:
            self.app_name = app_name
            super().__init__()

    def action_show_processes(self) -> None:
        self.push_screen(ProcessesModal())

    def on_manage_applications_modal_applications_updated(self, message: ManageApplicationsModal.ApplicationsUpdated):
        self.load_applications()

    def action_quit(self) -> None:
        """Quit the application if no processes are running."""
        running_apps = self.get_running_apps()
        if running_apps:
            app_names = ", ".join([app[0] for app in running_apps])
            self.notify(f"Cannot quit. Processes are still running: {app_names}", severity="error", timeout=5)
        else:
            self.exit()

if __name__ == "__main__":
    app = CondaLauncher()
    app.run()
