import pandas as pd

from src.opt.variables import USEFULL_CSV, IMPORTANT_COLUMNS


class DataAnnotations:
    annotations = {}

    def __init__(self, filename, **kwargs):
        self.file = filename
        self.checkup = kwargs.get('checkup', False)
        try:
            self.df = pd.read_csv(self.file, **kwargs)
        except Exception as err:
            print(err)
        try:
            self.df = self.df.drop(columns=USEFULL_CSV)
        except Exception as err:
            print(err)
            pass
        if self.checkup:
            self._checkup()
        self._file_annotations(self.df)

    def __len__(self):
        return self.annotations

    def __getitem__(self, item):
        return self.annotations[item]

    def __repr__(self):
        """
        :return: str, class representation
        """
        return str(self.annotations)

    def __iter__(self):
        """
        iterate on dict with generators
        :return: Tuples
        """
        self.n = 0
        yield from self.annotations.items()

    def _file_annotations(self, df: pd.DataFrame):
        regroup = df.groupby('Reference.1')['Name'].apply(list)
        for idx, values in regroup.items():
            self.annotations[idx] = values

    def _checkup(self):
        n = 0
        for col in IMPORTANT_COLUMNS:
            if self.df[col].isnull().values.any():
                n += 1
                print(f"You have in one or many empty cells in the {str(col)} column")
        if n > 1:
            raise ValueError(f"You have {str(n)} columns with empty cells. You need to check your file.")

    def get_row(self, uri: str, _id: str) -> pd.DataFrame:
        return self.df.loc[(self.df['Name'] == _id) & (self.df['Reference.1'] == uri)]

    def get_uri(self):
        return [annotation[0] for annotation in self.annotations]

