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
        return len(self.annotations)

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n <= self.__len__():
            self.n += 1
            for annotation in self.annotations:
                return annotation, self.annotations[annotation]
        else:
            raise StopIteration

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

    def get_row(self, _id: str) -> pd.DataFrame:
        return self.df[self.df['Name'] == _id]

