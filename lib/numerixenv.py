import os

def check():
    try:
        if os.environ['NUMERIX'] == 'numarray':
            raise EnvironmentError, "NUMERIX/numarray environment detected; numpy environment required"
    except KeyError:
        pass
