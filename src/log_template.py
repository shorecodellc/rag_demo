#kevin fink
#kevin@shorecode.org
#Mon Apr  6 09:49:55 AM +07 2026

import logging
import traceback
import os
import sys

class CustomLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)
    
    def trace(self, e):
        try:            
            self.error(f'Error: {e}, TB: {traceback.format_exc()}')
        except UnicodeEncodeError:
            try:                
                cleaned = str(traceback.format_exc()).encode("ascii", "ignore").decode()            
                self.error(f'Error: {e}, TB: {cleaned}')
            except UnicodeEncodeError:
                self.error(f'Error: TB: Unavailable due to unicode error')

def set_logging(name: str, filename: str) -> logging.Logger:
    """
    Creates a logging directory if one does not exist and initializes and configures a logger
    
    Args:
    name (str) : Name of the logger
    filename (str) : Name of the file to output the log to
    
    Returns:
    logging.Logger: Logger object
    """
    # Checks for a logging directory and creates one if it does not exist
    if getattr(sys, 'frozen', False):
        log_dir = os.path.join(os.path.dirname(sys.executable), 'logging')
    else:
        log_dir = os.path.join(os.path.dirname(__file__), 'logging')
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    # Create a logger
    custom = CustomLogger(name)
    custom.setLevel(logging.INFO)
                
    # Delete the logging file if it is greater than 10Mb
    try:
        # Get the size of the logging file
        file_size = os.path.getsize(filename)
        
        if file_size > 10000000:
            with open(filename, 'r', encoding='utf-8') as fn:
                old_log = fn.readlines()
            os.remove(filename)
            with open(filename, 'w', encoding='utf-8') as fn:
                fn.write(''.join(old_log[-80:]))
            with open(filename+'.bak', 'w', encoding='utf-8') as fn:
                fn.write(''.join(old_log))                
    except (PermissionError, FileNotFoundError):
        with open(filename, 'w', encoding='utf-8'):
            pass
        
    # File handler (for logging to file)
    file_handler = logging.FileHandler(filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s  - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    custom.addHandler(file_handler)  
        
    # You can also log messages to the console if needed
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Set the level for console output
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add the console handler to the logger
    custom.addHandler(console_handler)   

    return custom