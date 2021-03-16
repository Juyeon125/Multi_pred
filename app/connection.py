import pymysql


class Database:
    def __init__(self, host, user, password, database):
        self.conn = pymysql.connect(host=host, user=user, password=password, db=database, charset="utf8")

    def find_by_user_email(self, email):
        cursor = None
        sql = f"SELECT * FROM allec.user WHERE email = '{email}'"

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
        finally:
            cursor.close()

        if cursor.rowcount == 1:
            row = cursor.fetchall()

            row = row[0]
            user = {
                "user_idx": row[0],
                "email": row[1],
                "password": row[2],
                "created_date_time": row[3],
                "modified_date_time": row[4]
            }

            return user

        return None
