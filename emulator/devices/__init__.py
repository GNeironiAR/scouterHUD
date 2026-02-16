from devices.medical_monitor import MedicalMonitor
from devices.vehicle_obd2 import VehicleOBD2
from devices.server_infra import ServerInfra
from devices.home_thermostat import HomeThermostat
from devices.industrial_machine import IndustrialMachine

DEVICE_TYPES = {
    "medical.respiratory_monitor": MedicalMonitor,
    "medical.pulse_oximeter": MedicalMonitor,
    "medical.vital_signs": MedicalMonitor,
    "vehicle.obd2": VehicleOBD2,
    "infra.aws_instance": ServerInfra,
    "infra.server": ServerInfra,
    "home.thermostat": HomeThermostat,
    "home.temperature_sensor": HomeThermostat,
    "industrial.pressure_gauge": IndustrialMachine,
    "industrial.machine": IndustrialMachine,
}
