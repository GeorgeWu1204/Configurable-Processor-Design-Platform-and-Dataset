from .BOOM import BOOM_Chip_Tuner
from .RocketChip import Rocket_Chip_Tuner
from .EL2_VeeR import EL2_VeeR_Tuner

def get_chip_tuner(cpu_info):
    print(f"CPU Name: {cpu_info.cpu_name}")
    if cpu_info.cpu_name == "BOOM":
        return BOOM_Chip_Tuner(cpu_info)
    elif cpu_info.cpu_name == "RocketChip":
        return Rocket_Chip_Tuner(cpu_info)
    elif cpu_info.cpu_name == "EL2_VeeR":
        return EL2_VeeR_Tuner(cpu_info)

    else:
        raise ValueError(f"Unsupported CPU Name: {cpu_info.cpu_name}")