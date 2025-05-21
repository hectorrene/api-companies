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
    aws_access_key_id='ASIAUA4NCJJ5KJQ74W4A',
    aws_secret_access_key='mrrkPKwfS1TZjfMzqE3t2zVC0aIEm6plOY/SzjUq',
    aws_session_token='IQoJb3JpZ2luX2VjEAcaCXVzLXdlc3QtMiJHMEUCIQD9+UniRnHW10gN+eS87Ltwyv1ZQ9yZGps3zjMqATkFywIgDUT0/oWgdEEVSdt4Rnz5y/deKRKm4vaUgv2++qByuH0qvgIIwP//////////ARAAGgwyNzY3ODQzNjgyNTAiDEtV8mrWsq2NzA2bwCqSAnyDNWJh/OUP4c5QrU/ru/rXRFHBPTQ2pzrze6ZzNpnvjVob/OHmfTsS4Hk5pbG1z+1YZJzjBHuVY5ZgMikRunOUJqfv1faKuOuu1vx99DJA+MgMuruH3yXGNMu6qzJxTfffZ95K5l4tO1mVIXkDxJKNFH4QYXj/fyGo5QAGq8egkDsyDDipoESnqGZPAL6fyqEHly9/bxfBKffHqXAMNiO3yKvpw5QpDrj5YDXJMGS61N3D8I0Lo2JlTzcaIo7mKTWreBnCqBkgyJO+qpzR4nttwL0EdSlX2D441SNFEhgOZpaeyBtWPlDAXqUB83wAjA/An0PIp9OdoiVodPv1Rb1ldw4Ni7G9SYLH+yJGCy9V2ykwzs23wQY6nQEWNfB2ZuEjjRZddU6r2RaK6ZLAXD0Cmrlem8wps/vHy9/Jt8TZWJrEFIxNCFC8Hulu81hM4854s7LdNalxOxYPMPyUeZAor6CknA37Er7gI+yor/XEinyEOjayApHkudDxbsgWew7meJlJ/ceY9XCrhdBPRDRkd8Rm4dW9TrZ5WOT01PvE2UDjUouIxuAhWt534u7GmaDVg5S5ykXn',
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


api.add_resource(Companies, '/companies')
api.add_resource(addCompany, '/companies/add')
api.add_resource(updateCompany, '/companies/update/<int:id>')
api.add_resource(deleteCompany, '/comopanies/delete/<int:id>')
api.add_resource(AddEmployeeToCompany, '/companies/<int:company_id>/employees')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
