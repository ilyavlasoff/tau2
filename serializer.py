import numpy as np
import json


class Serializer:

    @staticmethod
    def serialize(path, data):
        if not isinstance(data, dict):
            raise Exception('Data has incorrect format')
        for i in data:
            if isinstance(data[i], np.ndarray):
                data[i] = data[i].tolist()
        try:
            file = open(path, 'w')
        except OSError:
            raise Exception('File not found')
        json.dump(data, file)

    @staticmethod
    def deserialize(path):
        try:
            file = open(path)
        except OSError:
            raise Exception('File not found')
        return json.load(file)