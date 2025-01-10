from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, LoadingIndicator
from textual.containers import ScrollableContainer
from textual.binding import Binding
from textual.reactive import reactive
from read_data import SystemDataCollector, SystemDataManager
import humanize
from datetime import datetime
from typing import Dict, Any

class SystemInfoWidget(Static):
    """Widget to display basic system information"""

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Loading...", id="system-info")

    def update_info(self, data: Dict[str, Any]) -> None:
        print(f"Updating {self.__class__.__name__}")
        try:
            platform_data = data["platform"]
            info_text = f"""[bold blue]System Information[/bold blue]
OS: {platform_data['system']} {platform_data['release']}
Version: {platform_data['version']}
Machine: {platform_data['machine']}
Processor: {platform_data['processor']}
Architecture: {platform_data['architecture'][0]}
Python Version: {platform_data['python_version'].split()[0]}
"""
            self.query_one("#system-info").update(info_text)
        except Exception as e:
            self.query_one("#system-info").update(f"[red]Error updating data: {str(e)}[/red]")

class HardwareInfoWidget(Static):
    """Widget to display hardware information"""

    def compose(self) -> ComposeResult:
        yield Static("Loading...", id="hardware-info")

    def update_info(self, data: Dict[str, Any]) -> None:
        try:
            hw_data = data["hardware"]
            cpu_data = hw_data["cpu"]
            memory_data = hw_data["memory"]

            info_text = f"""[bold green]Hardware Information[/bold green]
CPU Cores: {cpu_data['physical_cores']} Physical / {cpu_data['total_cores']} Logical
CPU Usage: {cpu_data['current_usage']}%
Memory Total: {humanize.naturalsize(memory_data['total'])}
Memory Used: {humanize.naturalsize(memory_data['used'])} ({memory_data['percent']}%)
Memory Available: {humanize.naturalsize(memory_data['available'])}
"""
            self.query_one("#hardware-info").update(info_text)
        except Exception as e:
            self.query_one("#hardware-info").update(f"[red]Error updating data: {str(e)}[/red]")

class NetworkInfoWidget(Static):
    """Widget to display network information"""

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static("Loading...", id="network-info")

    def update_info(self, data: Dict[str, Any]) -> None:
        print(f"Updating {self.__class__.__name__}")
        try:
            net_data = data["network"]
            info_text = f"""[bold yellow]Network Information[/bold yellow]
Hostname: {net_data['hostname']}
IP Address: {net_data['ip_address']}
MAC Address: {net_data['mac_address']}

[bold]Network Interfaces:[/bold]
"""
            for interface, addresses in net_data['network_interfaces'].items():
                info_text += f"\n{interface}:\n"
                for addr in addresses:
                    info_text += f"  - {addr['address']} ({addr['family']})\n"

            self.query_one("#network-info").update(info_text)
        except Exception as e:
            self.query_one("#network-info").update(f"[red]Error updating data: {str(e)}[/red]")

class ProcessTable(DataTable):
    """Table widget to display process information"""

    def on_mount(self) -> None:
        self.add_columns(
            "PID",
            "Name",
            "User",
            "Memory %"
        )

    def update_processes(self, processes: list) -> None:
        print(f"Updating {self.__class__.__name__}")
        try:
            self.clear()
            if not processes:
                self.add_row("No processes", "available", "", "")
                return

            sorted_processes = sorted(processes, key=lambda x: x.get('memory_percent', 0), reverse=True)[:20]
            for process in sorted_processes:
                self.add_row(
                    str(process.get('pid', 'N/A')),
                    str(process.get('name', 'Unknown')),
                    str(process.get('username', 'Unknown')),
                    f"{process.get('memory_percent', 0):.1f}%"
                )
        except Exception as e:
            self.clear()
            self.add_row("Error", f"Failed to update process data: {str(e)}", "", "")
class DiskUsageWidget(Static):
    """Widget to display disk usage information"""

    def compose(self) -> ComposeResult:
        yield Static("Loading...", id="disk-info")

    def update_info(self, data: Dict[str, Any]) -> None:
        print(f"Updating {self.__class__.__name__}")
        try:
            disk_data = data["hardware"]["disk"]
            info_text = "[bold magenta]Disk Usage[/bold magenta]\n"

            for device, info in disk_data.items():
                info_text += f"\n[bold]{device}[/bold] ({info['filesystem']})"
                info_text += f"\nMount: {info['mountpoint']}"
                info_text += f"\nTotal: {humanize.naturalsize(info['total'])}"
                info_text += f"\nUsed: {humanize.naturalsize(info['used'])} ({info['percent']}%)"
                info_text += f"\nFree: {humanize.naturalsize(info['free'])}\n"

            self.query_one("#disk-info").update(info_text)
        except Exception as e:
            self.query_one("#disk-info").update(f"[red]Error updating data: {str(e)}[/red]")

class SystemMonitorApp(App):
    """Main application class"""

    CSS = """
        Screen {
            background: #1f1f1f;
        }

        #top-container {
            height: 40vh;
            margin: 0;
        }

        #bottom-container {
            height: 50vh;
            margin: 0;
        }

        .info-widget {
            width: 1fr;
            height: 100%;
            margin: 1;
            padding: 1;
            border: solid $accent;
            background: $surface;
        }

        ProcessTable {
            width: 2fr;
            margin: 1;
            border: solid $accent;
            background: $surface;
        }

        DiskUsageWidget {
            width: 1fr;
            margin: 1;
            border: solid $accent;
            background: $surface;
        }

        LoadingIndicator {
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
        }
        """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh Data"),
        Binding("t", "toggle_refresh", "Toggle Auto-refresh"),
    ]

    REFRESH_INTERVAL = 5.0
    auto_refresh = reactive(True)

    def __init__(self):
        super().__init__()
        self.collector = SystemDataCollector()
        self.manager = SystemDataManager(self.collector)
        self.data = None

    def compose(self) -> ComposeResult:
        """Modified compose method with better structure"""
        yield Header()
        yield Static("Last Update: Never", id="timestamp")

        # Top container with system info widgets
        with Container(id="top-container"):
            with Horizontal():
                yield SystemInfoWidget(classes="info-widget")
                yield HardwareInfoWidget(classes="info-widget")
                yield NetworkInfoWidget(classes="info-widget")

        # Bottom container with process table and disk usage
        with Container(id="bottom-container"):
            with Horizontal():
                yield ProcessTable()
                yield DiskUsageWidget()

        yield Footer()

    async def on_mount(self) -> None:
        await self.refresh_data()
        self.set_interval(self.REFRESH_INTERVAL, self.refresh_data)
        self.notify("Press 'q' to quit, 'r' to refresh, 't' to toggle auto-refresh")

    async def refresh_data(self) -> None:
        if not self.auto_refresh:
            return

        loading = LoadingIndicator()
        self.mount(loading)

        try:
            self.data = self.manager.read_system_data()

            # Update all widgets with new data
            for widget_class in [SystemInfoWidget, HardwareInfoWidget, NetworkInfoWidget, DiskUsageWidget]:
                widget = self.query_one(widget_class)
                widget.update_info(self.data)

            process_table = self.query_one(ProcessTable)
            process_table.update_processes(self.data["process"]["running_processes"])

            timestamp = datetime.fromisoformat(self.data["timestamp"])
            self.query_one("#timestamp").update(f"Last Update: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            self.notify(f"Error refreshing data: {str(e)}", severity="error")
        finally:
            loading.remove()

    async def action_refresh(self) -> None:
        """Refresh all data"""
        await self.refresh_data()

    def action_toggle_refresh(self) -> None:
        """Toggle auto-refresh"""
        self.auto_refresh = not self.auto_refresh
        self.notify(f"Auto-refresh {'enabled' if self.auto_refresh else 'disabled'}")

if __name__ == "__main__":
    app = SystemMonitorApp()
    app.run()
