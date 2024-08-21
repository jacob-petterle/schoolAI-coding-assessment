


class Transform:

    def __init__(self):
        pass

    def transform_data(self, records: List[RawData]) -> List[TransformedData]:
        transformed_records = []
        for record in records: