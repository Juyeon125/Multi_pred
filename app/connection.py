import pymysql


class Database:
    def __init__(self, host, user, password, database):
        self.conn = pymysql.connect(host=host, user=user, password=password, db=database, charset="utf8")

    def find_by_user_email(self, email):
        cursor = None
        sql = "SELECT * FROM allec.user WHERE email = %s"
        var = (email)

        try:
            cursor = self.conn.cursor()
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

    def sign_up_user(self, name, email, password):
        cursor = None

        # 기존 이메일을 사용하는 유저가 존재하는지 체크
        user = self.find_by_user_email(email)
        if user is not None:
            return "exist email"

        # 삽입 쿼리문
        sql = f"INSERT INTO allec.user (`name`, `email`, `password`) VALUES (%s, %s, %s)"
        var = (name, email, password)

        # Insert 실행
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, var)
            self.conn.commit()
        finally:
            cursor.close()

        # 유저 정보 로딩
        return self.find_by_user_email(email)
