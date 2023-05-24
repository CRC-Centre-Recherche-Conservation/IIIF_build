import pandas as pd


class IIIF(object):
    pass


class Canvas(IIIF):
    pass


class Sequence(IIIF):
    pass


class Manifest(IIIF):
    pass


class Annotation(IIIF):
    scheme = {
        'Name': str,
        'Tags': list,
        'Dimensions': {
            'width': int,
            'height': int,
        },
        'Identifier': str,
        'Coordinates':
            {'x': float, 'y': float, 'w': float, 'h': float},
        'Value': str,
        'URI': str
    }

    @classmethod
    def data_annotation(cls, row: pd.DataFrame):
        return {
            'Name': row['Name'].values[0],
            'Tags': row['Tags'].values[0].split(','),
            'Dimensions': {
                'width': row['Dimensions'].values[0].split(',')[0],
                'height': row['Tags'].values[0].split(',')[1],
            },
            'Identifier': row['Identifier'].values[0],
            'Coordinates':
                {'x': row['X'].values[0], 'y': row['Y'].values[0], 'w': row['W'].values[0], 'h': row['H'].values[0]},
            'Value': row['Value'].values[0],
            'URI': row['Reference.1'].values[0]
        }
