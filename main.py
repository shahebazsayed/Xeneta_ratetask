from flask import Flask
from flask_restful import Api, Resource, reqparse
import postgresql
from datetime import datetime, timedelta


app = Flask(__name__)
api = Api(app)

db = postgresql.open('pq://user:password@host:port/database')


class rates(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('date_from', required=True)
        parser.add_argument('date_to', required=True)
        parser.add_argument('origin', required=True)
        parser.add_argument('destination', required=True)
        args = parser.parse_args()

        query = '''Select day,
        Case when total<3
        then null
        else round (avg_price, 2)
        END as average_price
        from (
            Select count(*) total,
                             day, orig_code,
                             dest_code, avg(price) avg_price
        from prices pr left join ports p
        ON pr.ORIG_CODE=p.CODE
        LEFT JOIN ports p1
        on pr.DEST_CODE=p1.CODE
        where(pr.orig_code=args.origin OR p.PARENT_SLUG=args.origin) and (pr.dest_code=args.destination OR p1.parent_slug=args.destination)
        and day between to_date(args.date_from,'yyyy-mm-dd') AND to_date(args.date_to,'yyyy-mm-dd') group by day, orig_code, dest_code);'''
        result = []
        date_from = datetime.strptime(args.date_from, '%Y-%m-%d')
        date_to = datetime.strptime(args.date_to, '%Y-%m-%d')
        diff_days = date_from - date_to
        days_diff = diff_days.days
        for i in range(days_diff):
            price = db.execute(query)
            days_price = date_from + timedelta(i)
            price_element = {
                "day" : days_price.strftime("%Y-%m-/%d"),
                "average_price" : price
            }
            result.append(price_element)

        return result, 200

# Add URL endpoints
api.add_resource(rates, '/rates')

if __name__ == '__main__':
    app.run()
