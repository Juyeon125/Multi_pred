import pymysql
from flask import current_app

from app.domain import Job, JobResult, EnzymeClass


class Database:
    host = None
    user = None
    password = None
    database = None

    conn = None

    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database

        self.connect_to_database()

        current_app.config['DB'] = self

    def __del__(self):
        if self.conn is not None:
            self.conn.close()

        self.conn = None

    def connect_to_database(self):
        self.conn = pymysql.connect(host=self.host, user=self.user, password=self.password, db=self.database,
                                    charset="utf8", autocommit=True)

    def get_cursor(self):
        if self.conn.open:
            return self.conn.cursor()
        else:
            self.connect_to_database()
            return self.conn.cursor()

    def find_user_by_user_email(self, email):
        cursor = None
        sql = "SELECT * FROM allec.user WHERE email = %s"
        var = (email)

        try:
            cursor = self.get_cursor()
            cursor.execute(sql, var)
        finally:
            cursor.close()

        if cursor.rowcount == 1:
            row = cursor.fetchall()

            row = row[0]
            user = {
                "user_idx": row[0],
                "name": row[1],
                "email": row[2],
                "password": row[3],
                "created_date_time": row[4],
                "modified_date_time": row[5]
            }

            return user

        return None

    def save_user(self, name, email, password):
        cursor = None

        # 기존 이메일을 사용하는 유저가 존재하는지 체크
        user = self.find_user_by_user_email(email)
        if user is not None:
            return "exist email"

        # 삽입 쿼리문
        sql = f"INSERT INTO allec.user (`name`, `email`, `password`) VALUES (%s, %s, %s)"
        var = (name, email, password)

        # Insert 실행
        try:
            cursor = self.get_cursor()
            cursor.execute(sql, var)
            self.conn.commit()
        finally:
            cursor.close()

        # 유저 정보 로딩
        return self.find_user_by_user_email(email)

    def save_job(self, job):
        cursor = None

        # Insert Query SQL
        sql = f"INSERT INTO allec.job (`idx`, `user_idx`, `req_sequences`) VALUES (%s, %s, %s)"
        var = (job['idx'], job['user_idx'], job['req_sequences'])

        try:
            cursor = self.get_cursor()
            cursor.execute(sql, var)
            self.conn.commit()
        finally:
            cursor.close()

        return job

    def find_job_by_idx(self, idx):
        cursor = None

        # Find Job SQL Query
        sql = "SELECT * FROM allec.job WHERE idx = %s"
        var = idx

        try:
            cursor = self.get_cursor()
            cursor.execute(sql, var)
        finally:
            cursor.close()

        if cursor.rowcount == 1:
            return Job(cursor.fetchone())

        return None

    def save_job_result(self, job_result):
        cursor = None

        # Insert Query SQL
        sql = f"INSERT INTO allec.job_result " \
              f"  (`job_idx`, `methods`, `query_id`, `query_description`, `sequence`, `ec_number`, `accuracy`) " \
              f"VALUES " \
              f"  (%s, %s, %s, %s, %s, %s, {job_result['accuracy']})"

        var = (job_result['job_idx'], job_result['methods'], job_result['query_id'], job_result['query_description'],
               job_result['sequence'], job_result['ec_number'])

        try:
            cursor = self.get_cursor()
            cursor.execute(sql, var)
            self.conn.commit()
        finally:
            cursor.close()

        return job_result

    def find_job_results_by_job_idx(self, job_idx):
        cursor = None

        # Find Job SQL Query
        sql = "SELECT * FROM allec.job_result WHERE job_idx = %s"
        var = job_idx

        try:
            cursor = self.get_cursor()
            cursor.execute(sql, var)
        finally:
            cursor.close()

        rows = cursor.fetchall()
        results = {
            "DeepEC": [],
            "ECPred": [],
            "DETECTv2": [],
            "eCAMI": [],
            "AllEC": []
        }

        for row in rows:
            jr = JobResult(row).__dict__
            if jr['ec_number'] is not None:
                entry = self.find_enzyme_class_by_ec_number(jr['ec_number'])
                if isinstance(entry, EnzymeClass):
                    jr['ec_number'] = entry.__dict__
                else:
                    jr['ec_number'] = {
                        "id": -1,
                        "ec_num": entry
                    }

            results[jr['methods']].append(jr)

        return results

    def find_enzyme_class_by_ec_number(self, ec_number):
        cursor = None

        sql = "SELECT * FROM enzyme WHERE ec_num = %s"
        var = ec_number

        try:
            cursor = self.get_cursor()
            cursor.execute(sql, var)
        finally:
            cursor.close()

        if cursor.rowcount == 1:
            return EnzymeClass(cursor.fetchone())

        return ec_number

    def find_all_enzyme(self):
        cursor = None
        sql = "select ec_num, accepted_name, reaction from enzyme order by class, subclass, subsubclass, serial"

        try:
            cursor = self.get_cursor()
            cursor.execute(sql)
        finally:
            cursor.close()

        if cursor.rowcount > 0:
            result_list = []
            row = cursor.fetchall()

            for row_val in row:
                result = {
                    "ec_number": row_val[0],
                    "accepted_name": row_val[1],
                    "reaction": row_val[2]
                }
                result_list.append(result)

            return result_list

        return []

    def find_all_history(self):
        cursor = None
        sql = "select * from predict_hist"

        try:
            cursor = self.get_cursor()
            cursor.execute(sql)
        finally:
            cursor.close()

        if cursor.rowcount > 0:
            result_list = []
            row = cursor.fetchall()

            for row_val in row:
                result = {
                    "sequence": row_val[1],
                    "method": row_val[2],
                    "ec_number": row_val[3],
                    "accepted_name": row_val[4],
                    "reaction": row_val[5],
                    "accuracy": row_val[6]
                }
                result_list.append(result)

            return result_list

        return []
