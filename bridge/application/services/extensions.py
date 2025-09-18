from flasgger import Swagger, swag_from
from flask_mail import Mail, Message


SWAGGER_TEMPLATE = {
    "securityDefinitions": {
        "apiKey": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Bearer Fabman API token"
        },
        "cronjob_token": {
            "type": "apiKey",
            "name": "CronjobToken",
            "in": "header",
            "description": "Token for railway cronjob verification"
        }
    },
    "security": [
        {
            "apiKey": []
        },
        {
            "cronjob_token": []
        }
    ],
    "info": {
        "title": "FabLab Bridge Swagger",
        "description": "OpenSource API with logic for online Fabman courses",
        "version": "1.0.0",
        "contact": {
            "name": "FabLab Brno",
            "url": "https://www.fablabbrno.cz/kontakt/"
        }
    }
}


# mail = Mail()
swagger = Swagger(template=SWAGGER_TEMPLATE)
