from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, ListView, ListItem, Button, Header, Footer, RichLog
from textual.binding import Binding
from textual.message import Message
from rich.text import Text
import psutil
import os

class ProcessesModal(Screen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Close"),
        Binding("ctrl+r", "refresh", "Refresh")
    ]

    def compose(self):
        yield Header()
        yield Horizontal(
            Vertical(
                Static("Running Applications", classes="section-title"),
                ListView(id="running_apps_list"),
                id="processes_modal"
            ),
            Vertical(
                Static("", id="output_title"),
                RichLog(id="process_output", wrap=True, markup=True, auto_scroll=False),
                id="output_sidebar",
                classes="hidden"
            ),
            id="processes_container"
        )
        yield Footer()

    def on_mount(self):
        self.update_running_apps()
        self.output_timer = self.set_interval(0.1, self.update_process_output)
        self.scroll_timer = self.set_interval(0.1, self.check_scroll_position)
        self.user_scrolled = False
        self.last_scroll_position = 0

    def on_unmount(self):
        self.output_timer.stop()
        self.scroll_timer.stop()

    def update_running_apps(self):
        running_apps = self.app.get_running_apps()
        running_apps_list = self.query_one("#running_apps_list", ListView)
        running_apps_list.clear()
        for app_name, pid in running_apps:
            running_apps_list.append(
                ListItem(
                    Horizontal(
                        Static(f"{app_name} (PID: {pid})", classes="app-info"),
                        Button("Kill", id=f"kill_{pid}", classes="action-button"),
                        Button("View", id=f"view_{pid}", classes="action-button"),
                        classes="list-item-content"
                    )
                )
            )
        
        # Check if the currently viewed process is still running
        if hasattr(self, 'current_pid') and not any(pid == self.current_pid for _, pid in running_apps):
            self.close_output_sidebar()

    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id
        if button_id.startswith("kill_"):
            pid = int(button_id.split("_")[1])
            self.kill_process(pid)
        elif button_id.startswith("view_"):
            pid = int(button_id.split("_")[1])
            self.toggle_process_output(pid)

    def action_refresh(self):
        self.update_running_apps()

    def kill_process(self, pid):
        try:
            process = psutil.Process(pid)
            app_name = next((name for name, p in self.app.running_processes.items() if p == pid), None)
            
            if app_name is None:
                # Check if this is a child process or a restarted process
                for name, initial_pid in self.app.running_processes.items():
                    if self.is_related_process(initial_pid, pid):
                        app_name = name
                        break
            
            if app_name is None:
                self.notify(f"Process with PID {pid} is not managed by this application.")
                self.update_running_apps()  # Refresh the list to remove any stale entries
                return

            def kill_proc_tree(proc, include_parent=True):
                children = proc.children(recursive=True)
                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                gone, still_alive = psutil.wait_procs(children, timeout=5)
                for p in still_alive:
                    try:
                        p.kill()
                    except psutil.NoSuchProcess:
                        pass
                if include_parent:
                    try:
                        proc.terminate()
                        proc.wait(5)
                    except psutil.NoSuchProcess:
                        pass

            kill_proc_tree(process)
            
            self.notify(f"Process {app_name} (PID: {pid}) and its children have been terminated.")
            
            # Remove the process from the app's running processes
            if app_name in self.app.running_processes:
                del self.app.running_processes[app_name]
            if app_name in self.app.process_outputs:
                del self.app.process_outputs[app_name]

            # Delete the associated .log file
            log_file = f"{app_name}.log"
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                    self.notify(f"Deleted log file: {log_file}")
                except Exception as e:
                    self.notify(f"Error deleting log file {log_file}: {str(e)}")

            # Close the sidebar if the killed process was being viewed
            if hasattr(self, 'current_pid') and self.current_pid == pid:
                self.close_output_sidebar()

            self.update_running_apps()  # Refresh the list immediately after killing a process

        except psutil.NoSuchProcess:
            self.notify(f"Process with PID {pid} not found.")
            self.update_running_apps()  # Refresh the list to remove any stale entries
        except psutil.AccessDenied:
            self.notify(f"Access denied when trying to terminate process with PID {pid}.")
        except Exception as e:
            self.notify(f"Error terminating process: {str(e)}")
            self.update_running_apps()  # Refresh the list to ensure it's up-to-date

    def is_related_process(self, initial_pid, current_pid):
        try:
            initial_process = psutil.Process(initial_pid)
            current_process = psutil.Process(current_pid)
            
            # Check if it's a child process
            if current_process in initial_process.children(recursive=True):
                return True
            
            # Check if it has the same name or command line
            if current_process.name() == initial_process.name():
                return True
            
            if len(current_process.cmdline()) > 1 and len(initial_process.cmdline()) > 1:
                if current_process.cmdline()[-1] == initial_process.cmdline()[-1]:
                    return True
            
            return False
        except psutil.NoSuchProcess:
            return False

    def toggle_process_output(self, pid):
        output_sidebar = self.query_one("#output_sidebar")
        if hasattr(self, 'current_pid') and self.current_pid == pid:
            self.close_output_sidebar()
        else:
            self.view_process_output(pid)

    def close_output_sidebar(self):
        output_sidebar = self.query_one("#output_sidebar")
        output_sidebar.add_class("hidden")
        if hasattr(self, 'current_pid'):
            delattr(self, 'current_pid')
        if hasattr(self, 'current_app_name'):
            delattr(self, 'current_app_name')

    def view_process_output(self, pid):
        output_sidebar = self.query_one("#output_sidebar")
        output_sidebar.remove_class("hidden")
        
        process_output = self.query_one("#process_output", RichLog)
        process_output.clear()
        
        try:
            process = psutil.Process(pid)
            self.current_app_name = next((app_name for app_name, app_pid in self.app.running_processes.items() if app_pid == pid), "Unknown")
            self.current_pid = pid
            
            output_title = self.query_one("#output_title", Static)
            output_title.update(f"Output for {self.current_app_name}")
            
            output = self.app.get_process_output(self.current_app_name)
            if output:
                process_output.write(Text(output))
                process_output.scroll_end(animate=False)
            else:
                process_output.write(Text("No output available.", style="italic"))
            
            self.user_scrolled = False
            
        except psutil.NoSuchProcess:
            process_output.write(Text(f"Process with PID {pid} not found.", style="red"))
        except psutil.AccessDenied:
            process_output.write(Text(f"Access denied when trying to access process with PID {pid}.", style="red"))

    def update_process_output(self):
        if hasattr(self, 'current_app_name') and hasattr(self, 'current_pid'):
            process_output = self.query_one("#process_output", RichLog)
            new_output = self.app.get_process_output(self.current_app_name)
            if new_output:
                current_content = process_output.render()
                if new_output != current_content:
                    process_output.clear()
                    process_output.write(Text(new_output))
                    if not self.user_scrolled:
                        process_output.scroll_end(animate=False)

    def on_process_output_updated(self, message: Message):
        if hasattr(self, 'current_app_name') and hasattr(message, 'app_name') and message.app_name == self.current_app_name:
            self.update_process_output()

    def on_conda_launcher_process_output_updated(self, message: Message):
        if hasattr(self, 'current_app_name') and hasattr(message, 'app_name') and message.app_name == self.current_app_name:
            self.update_process_output()
        if message.app_name not in [app_name for app_name, _ in self.app.get_running_apps()]:
            self.update_running_apps()  # Refresh the list when a new process is added

    def check_scroll_position(self):
        if hasattr(self, 'current_app_name') and hasattr(self, 'current_pid'):
            process_output = self.query_one("#process_output", RichLog)
            current_scroll = process_output.scroll_y
            
            if current_scroll < self.last_scroll_position:
                # Scrolled up
                self.user_scrolled = True
            elif current_scroll >= process_output.max_scroll_y:
                # Scrolled to bottom
                self.user_scrolled = False
            
            self.last_scroll_position = current_scroll
