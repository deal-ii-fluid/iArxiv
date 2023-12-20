import logging
import colorlog

class ColoredLogger:
    def __init__(self):
        log_format = (
            '%(log_color)s%(levelname)-8s'
            '[%(module)s:%(lineno)d] '
            '%(reset)s%(message)s'
        )

        formatter = colorlog.ColoredFormatter(
            log_format,
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red'
            }
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        self.logger = logger
    
    def info(self, message):
        self.logger.info(message)
        
    def warning(self, message):
         self.logger.warning(message)
         
    def error(self, message):
        self.logger.error(message)
        
    # do same for debug, critical etc as per your need

