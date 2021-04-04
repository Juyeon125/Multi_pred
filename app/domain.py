class Job:
    def __init__(self, row):
        self.idx = row[0]
        self.user_idx = row[1]
        self.req_sequences = row[2]
        self.status = row[3]
        self.created_datetime = row[4]
        self.modified_datetime = row[5]


class JobResult:
    def __init__(self, row):
        self.idx = row[0]
        self.job_idx = row[1]
        self.methods = row[2]
        self.query_id = row[3]
        self.query_description = row[4]
        self.sequence = row[5]
        self.ec_number = row[6]
        self.accuracy = row[7]
        self.created_datetime = row[8]
        self.modified_datetime = row[9]


class EnzymeClass:
    def __init__(self, row):
        self.id = row[0]
        self.ec_num = row[1]
        self.accepted_name = row[2]
        self.reaction = row[3]
        self.other_names = row[4]
        self.sys_name = row[5]
        self.comments = row[6]
        self.links = row[7]
