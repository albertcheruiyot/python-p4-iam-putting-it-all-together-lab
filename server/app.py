#!/usr/bin/env python3

from flask import request, session, jsonify, make_response
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        new_username = data.get('username')
        new_image_url = data.get('image_url')
        new_bio = data.get('bio')

        if not new_username or len(new_username) < 1:
            response = make_response({"error" : "Username must not be empty"}, 422)
            return response
        elif User.query.filter(User.username == new_username).first():
            response = make_response({"error": "Username must be unique"}, 422)
            return response
        else:
            new_validated_username = new_username

        new_user = User(
            username = new_validated_username, 
            bio = new_bio,
            image_url = new_image_url
        )

        new_user.password_hash = data.get('password')

        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id

        new_user_dict = new_user.to_dict()
        response = make_response(new_user_dict, 201)
        return response
        

class CheckSession(Resource):
    def get(self):
        user = User.query.filter(User.id == session.get("user_id")).first()
        if user:
            user_dict = user.to_dict()
            response = make_response(user_dict, 200)
            return response
        else:
            response_dict = {"error" : "Unauthorized: please login"}
            response = make_response(response_dict, 401)
            return response
    
class Login(Resource):
    def post(self):
        data = request.get_json()
        the_username = data.get('username')
        the_password = data.get('password')
        user = User.query.filter(User.username == the_username).first()

        if user and user.authenticate(the_password):
            session["user_id"] = user.id
            user_dict = user.to_dict()
            response = make_response(user_dict, 200)
            return response
        else:
            response_dict = {"error" : "Unauthorized: wrong username/password"}
            response = make_response(response_dict, 401)
            return response

class Logout(Resource):
    def delete(self):
        if session["user_id"]:

            session["user_id"] = None
            return make_response({}, 204)
        else:
            response_dict = {"error" : "Unauthorized. You need to login to logout"}
            response = make_response(response_dict, 401)
            return response

class RecipeIndex(Resource):
    def get(self):
        if "user_id" not in session:
            resp_dict = {"error": "Please login"}
            response = make_response(jsonify(resp_dict), 401)
            return response

        try:
            user = User.query.filter(User.id == session["user_id"]).first()
            if not user:
                resp_dict = {"error": "User not found"}
                response = make_response(jsonify(resp_dict), 401)
                return response

        
            recipe_list = [recipe.to_dict() for recipe in user.recipes]

            response_dict = {
                "recipes": recipe_list,
                "user": user.to_dict()
            }

            return make_response(jsonify(response_dict), 200)
        except Exception as e:
            response = make_response({"error": str(e)}, 500)
            return response

    def post(self):
        if "user_id" not in session:
            resp_dict = {"error": "Please login"}
            response = make_response(jsonify(resp_dict), 401)
            return response

        data = request.get_json()
        new_title = data.get('title')
        new_instructions = data.get('instructions')
        new_minutes_to_complete = data.get('minutes_to_complete')

        if not new_title or len(new_title) < 1:
            resp_dict = {"error": "The title should not be empty"}
            response = make_response(jsonify(resp_dict), 422)
            return response

        if not new_instructions or len(new_instructions) < 50:
            resp_dict = {"error": "The instructions should be at least 50 characters long"}
            response = make_response(jsonify(resp_dict), 422)
            return response

        if not isinstance(new_minutes_to_complete, int):
            resp_dict = {"error": "Minutes to complete should be an integer"}
            response = make_response(jsonify(resp_dict), 422)
            return response

        try:
            user = User.query.filter(User.id == session["user_id"]).first()
            if not user:
                resp_dict = {"error": "User not found"}
                response = make_response(jsonify(resp_dict), 401)
                return response

            new_recipe = Recipe(
                title=new_title,
                instructions=new_instructions,
                minutes_to_complete=new_minutes_to_complete
            )

        
            user.recipes.append(new_recipe)

            db.session.add(new_recipe)
            db.session.commit()

            response_dict = {
                "title": new_recipe.title,
                "instructions": new_recipe.instructions,
                "minutes_to_complete": new_recipe.minutes_to_complete,
                "user": user.to_dict()
            }

            return make_response(jsonify(response_dict), 201)
        except Exception as e:
            db.session.rollback()
            response = make_response({"error": str(e)}, 500)
            return response



api.add_resource(Signup, '/signup')
api.add_resource(Login, '/login')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Logout, '/logout')
api.add_resource(RecipeIndex, '/recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)


