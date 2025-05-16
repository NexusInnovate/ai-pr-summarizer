# LOW SEVERITY: Unsafe Deserialization and Other Minor Issues
# File: src/utils/data_processor.py

import pickle
import yaml
import json
import logging
import tempfile
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.data_cache = {}
    
    # LOW SEVERITY: Unsafe deserialization with pickle
    def load_object_from_file(self, file_path):
        """
        Load a Python object from a pickle file.
        WARNING: pickle.load can execute arbitrary code!
        """
        try:
            with open(file_path, 'rb') as file:
                # Unsafe: pickle.load can execute arbitrary code
                data = pickle.load(file)
            return data
        except Exception as e:
            logger.error(f"Failed to load object from {file_path}: {e}")
            return None
    
    # LOW SEVERITY: Unsafe YAML loading
    def parse_yaml_config(self, yaml_string):
        """
        Parse YAML configuration string.
        """
        try:
            # Unsafe: yaml.load can execute arbitrary code 
            # with PyYAML versions prior to 5.1
            config = yaml.load(yaml_string)
            return config
        except Exception as e:
            logger.error(f"Failed to parse YAML: {e}")
            return {}
    
    # LOW SEVERITY: Temporary file creation without secure permissions
    def create_temp_file(self, data):
        """
        Create a temporary file with some data.
        """
        try:
            # Insecure: creates temp file without secure permissions
            temp_file = tempfile.mktemp()
            with open(temp_file, 'w') as f:
                f.write(data)
            
            logger.info(f"Created temporary file at {temp_file}")
            return temp_file
        except Exception as e:
            logger.error(f"Failed to create temporary file: {e}")
            return None
    
    # POTENTIALLY LOW SEVERITY: Logging potentially sensitive information
    def process_user_data(self, user_data):
        """
        Process user data and log details.
        """
        try:
            # Potentially logs sensitive information
            logger.info(f"Processing data for user: {user_data}")
            
            # Do some processing...
            result = self._transform_data(user_data)
            
            return result
        except Exception as e:
            # Error logging might include sensitive data
            logger.error(f"Error processing user data {user_data}: {e}")
            return None
    
    def _transform_data(self, data):
        """Transform input data."""
        # Dummy implementation
        return {k: v.upper() if isinstance(v, str) else v for k, v in data.items()}


# Usage example
if __name__ == "__main__":
    processor = DataProcessor()
    
    # Unsafe deserialization example
    # data = processor.load_object_from_file("user_data.pickle")
    
    # Unsafe YAML parsing
    yaml_str = """
    server:
      host: localhost
      port: 8080
    database:
      username: admin
      password: secret123
    """
    config = processor.parse_yaml_config(yaml_str)
    print(config)
    
    # Insecure temporary file
    temp_path = processor.create_temp_file("This is some data")
    if temp_path:
        os.remove(temp_path)  # Clean up
    
    # Potentially logs sensitive data
    user = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "ssn": "123-45-6789",  # Sensitive!
        "credit_card": "4111-1111-1111-1111"  # Sensitive!
    }
    processor.process_user_data(user)