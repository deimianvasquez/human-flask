"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, Human
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
db_url = os.getenv('DATABASE_URL')
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)



@app.route('/humans', methods=['GET'])
@app.route('/humans/<int:user_id>', methods=['GET'])
def handle_humans(user_id = None):
    if request.method == 'GET':
        if user_id is None:
            humans = Human()
            humans = humans.query.all()
            
            return jsonify(list(map(lambda item: item.serialize(), humans))) , 200
        else:
            human = Human()
            human = human.query.get(user_id)
            if human:
                return jsonify(human.serialize())
            
        return jsonify({"message":"not found"}), 404


@app.route('/humans', methods=['POST'])
def add_new_human():
    if request.method == 'POST':
        body = request.json
        if  body.get("name") is None:
            return {"message":"error propertie bad "} ,400

        if body.get("lastname") is None:
            return jsonify({"message":"error propertie bad "}), 400

        if body.get("email") is None:
            return jsonify({"message":"error propertie bad "} ), 400

        new_human = Human(name=body["name"], lastname=body.get("lastname"), email=body["email"])
        db.session.add(new_human)

        try:
            db.session.commit()
            return jsonify(new_human.serialize()), 201
        except Exception as error:
            print(error.args)
            db.session.rollback()
            return jsonify({"message":f"Error {error.args}"}),500


@app.route('/humans', methods=['PUT'])#actualizar
@app.route('/humans/<int:human_id>', methods=['PUT'])#actualizar
def update_human(human_id=None):
    if request.method == 'PUT':
        body = request.json
        
        if human_id is None:
            return jsonify({"message":"Bad request"}), 400

        if human_id is not None:
            update_human = Human.query.get(human_id)
            if update_human is None:
                return jsonify({"message":"Not found"}), 404
            else:
                update_human.name = body["name"]
                update_human.lastname = body["lastname"]
                update_human.email = body["email"]

                try:
                    db.session.commit()
                    return jsonify(update_human.serialize()), 201
                except Exception as error:
                    print(error.args)
                    return jsonify({"message":f"Error {error.args}"}),500

        return jsonify([]), 200
    return jsonify([]), 405


@app.route('/humans', methods=['DELETE'])
@app.route('/humans/<int:human_id>', methods=['DELETE'])
def delete_human(human_id=None):
    if request.method == 'DELETE':
        if human_id is None:
            return jsonify({"message":"Not found"}), 400

        if human_id is not None:
            delete_human = Human.query.get(human_id)
            
            if delete_human is None:
                return jsonify({"message":"Not found"}), 404
            else:
                db.session.delete(delete_human)

                try:
                    db.session.commit()
                    return jsonify([]), 204
                except Exception as error:
                    print(error.args)
                    db.session.rollback()
                    return jsonify({"message":f"Error {error.args}"}),500
        
    return jsonify([]), 405
     

   
# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
