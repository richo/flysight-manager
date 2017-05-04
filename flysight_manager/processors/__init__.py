from .gswoop import gSwoopProcessor


def get_processor(name):
    return {
        'gswoop': gSwoopProcessor,
    }[name]
