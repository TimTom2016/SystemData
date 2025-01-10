from datetime import datetime
import platform
import psutil
import os
import sys
import socket
import uuid
import json
from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, asdict

class NetworkAddress(TypedDict):
    address: str
    netmask: Optional[str]
    family: str

class CPUFrequency(TypedDict):
    current: float
    min: float
    max: float

class ProcessInfo(TypedDict):
    pid: int
    name: str
    username: str
    memory_percent: float

class DiskInfo(TypedDict):
    mountpoint: str
    filesystem: str
    total: int
    used: int
    free: int
    percent: float

@dataclass
class PlatformData:
    system: str
    release: str
    version: str
    machine: str
    processor: str
    architecture: tuple[str, str]
    python_version: str

@dataclass
class NetworkData:
    hostname: str
    ip_address: str
    mac_address: str
    network_interfaces: Dict[str, List[NetworkAddress]]

@dataclass
class CPUData:
    physical_cores: int
    total_cores: int
    max_frequency: Optional[CPUFrequency]
    current_usage: float

@dataclass
class MemoryData:
    total: int
    available: int
    used: int
    percent: float

@dataclass
class HardwareData:
    cpu: CPUData
    memory: MemoryData
    disk: Dict[str, DiskInfo]

@dataclass
class ProcessData:
    total_processes: int
    running_processes: List[ProcessInfo]

@dataclass
class SystemData:
    timestamp: str
    platform: PlatformData
    network: NetworkData
    hardware: HardwareData
    process: ProcessData

class SystemDataCollector:
    """Class responsible for collecting system data"""

    @staticmethod
    def get_network_interfaces() -> Dict[str, List[NetworkAddress]]:
        interfaces: Dict[str, List[NetworkAddress]] = {}
        for interface, addresses in psutil.net_if_addrs().items():
            interfaces[interface] = []
            for addr in addresses:
                addr_info: NetworkAddress = {
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "family": str(addr.family)
                }
                interfaces[interface].append(addr_info)
        return interfaces

    @staticmethod
    def get_cpu_frequency() -> Optional[CPUFrequency]:
        try:
            cpu_freq = psutil.cpu_freq()
            return {
                "current": cpu_freq.current,
                "min": cpu_freq.min,
                "max": cpu_freq.max
            }
        except:
            return None

    @staticmethod
    def get_disk_info() -> Dict[str, DiskInfo]:
        disks: Dict[str, DiskInfo] = {}
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks[partition.device] = {
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                }
            except:
                continue
        return disks

    @staticmethod
    def get_running_processes() -> List[ProcessInfo]:
        processes: List[ProcessInfo] = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent']):
            try:
                processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "username": proc.info['username'],
                    "memory_percent": proc.info['memory_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes

    def collect(self) -> SystemData:
        """Collect all system data and return as SystemData object"""

        platform_data = PlatformData(
            system=platform.system(),
            release=platform.release(),
            version=platform.version(),
            machine=platform.machine(),
            processor=platform.processor(),
            architecture=platform.architecture(),
            python_version=sys.version
        )

        network_data = NetworkData(
            hostname=socket.gethostname(),
            ip_address=socket.gethostbyname(socket.gethostname()),
            mac_address=':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                for elements in range(0,2*6,2)][::-1]),
            network_interfaces=self.get_network_interfaces()
        )

        cpu_data = CPUData(
            physical_cores=psutil.cpu_count(logical=False),
            total_cores=psutil.cpu_count(logical=True),
            max_frequency=self.get_cpu_frequency(),
            current_usage=psutil.cpu_percent(interval=1)
        )

        memory = psutil.virtual_memory()
        memory_data = MemoryData(
            total=memory.total,
            available=memory.available,
            used=memory.used,
            percent=memory.percent
        )

        hardware_data = HardwareData(
            cpu=cpu_data,
            memory=memory_data,
            disk=self.get_disk_info()
        )

        process_data = ProcessData(
            total_processes=len(psutil.pids()),
            running_processes=self.get_running_processes()
        )

        return SystemData(
            timestamp=datetime.now().isoformat(),
            platform=platform_data,
            network=network_data,
            hardware=hardware_data,
            process=process_data
        )

class SystemDataManager:
    """Class responsible for managing system data operations"""

    def __init__(self, collector: SystemDataCollector):
        self.collector = collector

    def read_system_data(self) -> Dict[str, Any]:
        """Read system data and return as dictionary"""
        try:
            system_data = self.collector.collect()
            return asdict(system_data)
        except Exception as e:
            return {"error": f"Failed to collect system data: {str(e)}"}

    def save_to_file(self, data: Dict[str, Any], filename: str = "system_data.json") -> None:
        """Save the collected data to a JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

def main() -> None:
    collector = SystemDataCollector()
    manager = SystemDataManager(collector)

    data = manager.read_system_data()
    manager.save_to_file(data)
    print("System data has been collected and saved to system_data.json")

if __name__ == "__main__":
    main()
