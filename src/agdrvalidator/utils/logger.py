import logging 

def setUp(name, level=logging.ERROR):
#def setUp(name, level=logging.INFO):
#def setUp(name, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level) # default level is WARNING
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(lineno)d: %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger