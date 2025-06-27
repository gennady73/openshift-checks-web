import yq
# Test from commandline: python3 -m yq -Y --in-place '.metadata.name="xxx"' ./modules/install-config.yaml

# Specify the path to your YAML file
yaml_file_path = "./install-config.yaml"

# Specify the key and new value you want to replace
key_to_replace = '.metadata.name'
new_value = 'CRC.xxx.yyy'

# Build the yq command to replace the value
yq_command = ["-Y", "--in-place", f"{key_to_replace}=\"{new_value}\"", f"{yaml_file_path}"]


def run_yq_cli():
    # Run the yq command
    # yq.cli(args=["-Y", "--in-place", f"{key_to_replace}=\"{new_value}\"", f"{yaml_file_path}"])
    yq.cli(args=yq_command)


if __name__ == '__main__':
    run_yq_cli()
