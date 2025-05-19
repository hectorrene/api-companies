from flask import Flask, request    
from flask_restful import Resource, Api
import boto3
import json

app = Flask(__name__)
api = Api(app)

companies = { 
    1: {'name' : 'Furukawa', 'location' : 'JAP', 'compIdent' : '1'},
    2: {'name' : 'Telmex', 'location' : 'MEX', 'compIdent' : '2'},
    3: {'name' : 'Ikea', 'location' : 'SWE', 'compIdent' : '3'},
    4: {'name' : 'Temu', 'location' : 'CHN', 'compIdent' : '4'},
    5: {'name' : 'Apple', 'location' : 'USA', 'compIdent' : '5'},
}

sqs = boto3.client(
    'sqs',
    region_name='us-east-1',
    aws_access_key_id='ASIAUA4NCJJ5EXLOZPZU',
    aws_secret_access_key='MbEYaULuSgpG9ehBmj0OwA3KuZlRYw4h+L2N/YBS',
    aws_session_token='IQoJb3JpZ2luX2VjENn//////////wEaCXVzLXdlc3QtMiJHMEUCIHcCPNZ0cPt+5hC6fnwEcvfjUhc+lzzvdNUJAfD8KeOSAiEA8dZrO+NZFnTl9Fl1pZaAzGSsdpwOUcwzwS9f/Z9PYscqvgIIkv//////////ARAAGgwyNzY3ODQzNjgyNTAiDP8zzPNKnjY7WxM4TyqSAl39CDuR+BI11gV9iSBDt3B1NHv6UZc0AY4UHh+iMB/0lHIZyKSVJncifTZIhM3xuZqMhHc5ImDn4EAo5iN7uzi8XG4mUTzxO72Uar+7DezNZu31BafsdM5yq6JpMXeUBq1Bdf5ri8/D7l9JNVPikcQfe3emWmOANSEpQIXixgCC5E6DJj9iNnDLc9Pn+iEeNmV7omWRRGGkCHZ+BYI3lP/FBw7APjWVY2J2iMMP37eO+85QUP49NXZo1ZYXQb3CFiTXX2UujvFT0fH+0AY1WlPjMibH3LKP2ZKrZfndJGVn59YZdcHAUJrrOBCZjz1PFw4fuaK8pJ7CKIYd4WnrPt2W4YY7NYRtHODBcAtayqAOKiYwh7+twQY6nQGjg3eyO1ORCuOrIST5C2LL9eM9yNxZJHkFN6FcRHAFq8ajwQFd2vqGPQXq2tANPZcDuSSDyjd3+yj2WwKnqhoE326OVEkZvZEfip6XJTtfU8v5XuLRI9BanrT9T3gDadYd54xKqEr3DgzRCRU4pW8NdFabdbZTejVL3FElBXVhOeMVDmbntQFQkB/PaS7ukfjTByVJi1HCvguHWXky',
)

queue_url = 'https://sqs.us-east-1.amazonaws.com/276784368250/my-api-queue'

class Companies(Resource):
    def get(self):
        return companies

class addCompany(Resource):
    def post(self):
        data = request.get_json()
        new_id = max(companies.keys(), default=0) + 1
        companies[new_id] = {
            'name' : data.get('name'), 
            'location' : data.get('location'),
            'compIdent' : new_id,
        }

        return {'id': new_id, 'company' : companies[new_id]}, 201

class updateCompany (Resource):
    def put(self, id):
        if id in companies:
            data = request.get_json()
            companies[id]['name'] = data.get('name', companies[id]['name'])
            companies[id]['location'] = data.get('location', companies[id]['location'])
            companies[id]['compIdent'] = data.get('compIdent', companies[id]['compIdent'])
            return {'message': 'Company updated', 'company': companies[id]}, 200
        return {'message': 'Company not found'}, 404

class deleteCompany(Resource): 
    def delete(self, id):
        if id in companies:
            deleted = companies.pop(id)
            return {'message': 'Company deleted', 'deleted': deleted}, 200
        return {'message': 'Company not found'}, 404

class AddEmployeeToCompany(Resource):
    def post(self, company_id):
        if company_id not in companies:
            return {'message': 'Company not found'}, 404

        data = request.get_json()
        name = data.get('name')

        if not name:
            return {'message': 'Missing employee name'}, 400

        message = {
            'action': 'create_employee',
            'payload': {
                'name': name,
                'companyId': str(company_id)
            }
        }

        try:
            response = sqs.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message)
            )
            return {
                'message': f'Employee "{name}" queued for company ID {company_id}',
                'sqsMessageId': response.get('MessageId')
            }, 202
        except Exception as e:
            return {'message': 'Failed to send message', 'error': str(e)}, 500


api.add_resource(Companies, '/')
api.add_resource(addCompany, '/add')
api.add_resource(updateCompany, '/update/<int:id>')
api.add_resource(deleteCompany, '/delete/<int:id>')
api.add_resource(AddEmployeeToCompany, '/companies/<int:company_id>/employees')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
