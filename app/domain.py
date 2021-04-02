class Job:
    def __init__(self, row):
        self.idx = row[0]
        self.user_idx = row[1]
        self.req_sequences = row[2]
        self.created_datetime = row[3]
        self.modified_datetime = row[4]


class JobResult:
    def __init__(self, row):
        self.idx = row[0]
        self.job_idx = row[1]
        self.methods = row[2]
        self.query_id = row[3]
        self.sequence = row[4]
        self.ec_number = row[5]
        self.created_datetime = row[6]
        self.modified_datetime = row[7]
