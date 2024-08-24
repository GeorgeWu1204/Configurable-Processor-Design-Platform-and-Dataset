class config_param:
    def __init__(self, name, type, value):
        self.name = name
        self.type = type
        self.value = value


class object_cpu_info:
    def __init__(self, name, config_params, output_params, target_fpga):
        self.name = name
        self.config_params = config_params
        self.output_params = output_params
        self.target_fpga = target_fpga
    
