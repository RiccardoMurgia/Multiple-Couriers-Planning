import json
import os


class Json_parser:
    # Define the paths for each approach's result folder
    def __init__(self, result_directory_path: 'str' = 'res'):

        self.result_directory_path = result_directory_path
        self.approach_folders = {
            "mip": os.path.join(result_directory_path, "mip"),
            "sat": os.path.join(result_directory_path, "sat"),
            "cp": os.path.join(result_directory_path, "cp"),
            "smt": os.path.join(result_directory_path, "smt")
        }

    def save_results(self, approach_name, instance_number, result):

        # Create the approach's result folder if it doesn't exist
        if approach_name in self.approach_folders:
            if not os.path.exists(self.approach_folders[approach_name]):
                os.makedirs(self.approach_folders[approach_name])

        # Save the result to a JSOinstance.origin file
        instance_path = os.path.join(self.approach_folders[approach_name], f"{instance_number}.json")
        with open(instance_path, "w") as json_file:
            json_file.write(json.dumps({approach_name: result}, indent=4))

