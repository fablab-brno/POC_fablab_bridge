TYPE_JSON = "application/json"


example_training_course = {
    "account": 1,
    "createdAt": "2017-06-29T12:25:20.095Z",
    "defaultDuration": 0,
    "defaultDurationUnit": "month",
    "id": 1,
    "lockVersion": 1,
    "metadata": None,
    "notes": None,
    "state": "active",
    "title": "Example Course",
    "updatedAt": "2023-01-30T15:02:17.445Z",
    "updatedBy": 1
}

example_embedded_course = {
    "trainingCourse": example_training_course
}

cm_test = {
    "test_id": 1234567,
    "test_name": "Test Online Course"
}

cm_link = {
    "link_id": 1234567,
    "link_name": "Test (Test Online Course)",
    "link_url_id": ""
}

cm_result = {
    "link_result_id": 12345678,
    "first": "",
    "last": "",
    "email": "",
    "percentage": 75,
    "points_scored": 3,
    "points_available": 4,
    "requires_grading": "No",
    "time_started": 1692968162,
    "time_finished": 1692968239,
    "duration": "00:01:17",
    "percentage_passmark": "75",
    "passed": True,
    "feedback": "",
    "give_certificate_only_when_passed": False,
    "certificate_url": "",
    "certificate_serial": "",
    "view_results_url": "",
    "access_code_question": "",
    "access_code_used": "",
    "extra_info_question": "",
    "extra_info_answer": "",
    "cm_user_id": "encrypted<membed_id-training_id>",
    "ip_address": "0"
}

cm_hook_body = {
    "payload_type": "single_user_test_results_link",
    "payload_status": "live",
    "test": cm_test,
    "link": cm_link,
    "result": cm_result
}

training_urls_inputs = {
    "type": "object",
    "required": [
        "member_id",
        "training_id"
    ],
    "properties": {
        "member_id": {
            "type": "integer",
            "description": "Member ID from Fabman"
        },
        "training_id": {
            "type": "integer",
            "description": "Training-course ID from Fabman"
        }
    },
    "example": {
        "member_id": 123456,
        "training_id": 1234
    }
}

training_urls_outputs = {
    "type": "object",
    "properties": {
        "quiz_url": {
            "type": "string",
            "description": "Full URL to CM quiz"
        },
        "yt_url": {
            "type": "string",
            "description": "YouTube video URL"
        },
        "wiki_url": {
            "type": "string",
            "description": "FL wiki URL of"
        },
        "title": {
            "type": "string",
            "description": "Name of training"
        }
    },
    "example": {
        "quiz_url": "https://www.classmarker.com/online-test/start/?quiz=XXX&cm_user_id=encrypted<membed_id-training_id>",
        "yt_url": "https://www.yt.com/test_url",
        "wiki_url": "https://www.wiki.com/test_url",
        "title": "Test training"
    }
}

training_urls_schema = {
    "tags": [
        "MemberTrainingsData"
    ],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "type": "object",
            "required": True,
            "schema": {
                "$ref": "#/definitions/TrainingURLSInputs"
            }
        }
    ],
    "consumes": [
        TYPE_JSON
    ],
    "produces": [
        TYPE_JSON
    ],
    "deprecated": False,
    "definitions": {
        "TrainingURLSInputs": training_urls_inputs,
        "TrainingURLSOuputs": training_urls_outputs
    },
    "responses": {
        "200": {
            "description": "Full URL for online course",
            "schema": {
                "$ref": "#definitions/TrainingURLSOuputs"
            }
        }
    }
}

absolved_trainings_schema = {
    "tags": [
        "MemberTrainingsData"
    ],
    "parameters": [
        {
            "name": "member_id",
            "in": "path",
            "type": "integer",
            "required": True
        }
    ],
    "consumes": [
        "text/plain"
    ],
    "produces": [
        TYPE_JSON
    ],
    "deprecated": False,
    "definitions": {
        "Training": {
            "type": "object",
            "properties": {
                "account": {
                    "type": "integer"
                },
                "createdAt": {
                    "type": "string"
                },
                "defaultDuration": {
                    "type": "integer"
                },
                "defaultDurationUnit": {
                    "type": "string"
                },
                "id": {
                    "type": "integer"
                },
                "lockVersion": {
                    "type": "integer"
                },
                "metadata": {
                    "type": "object",
                },
                "notes": {
                    "type": "string"
                },
                "state": {
                    "type": "string"
                },
                "title": {
                    "type": "string"
                },
                "updatedAt": {
                    "type": "string"
                },
                "updatedBy": {
                    "type": "integer"
                }
            },
            "example": example_training_course
        },
        "Embedded": {
            "type": "object",
            "properties": {
                "trainingCourse": {
                    "$ref": "#/definitions/Training"
                }
            },
            "example": {
                "trainingCourse": example_training_course
            }
        },
        "EmbeddedTrainingCourse": {
            "type": "object",
            "properties": {
                "_embedded": {
                    "$ref": "#/definitions/Embedded"
                },
                "createdAt": {
                    "type": "string"
                },
                "date": {
                    "type": "string"
                },
                "fromDate": {
                    "type": "string"
                },
                "id": {
                    "type": "string"
                },
                "lockVersion": {
                    "type": "string"
                },
                "notes": {
                    "type": "string"
                },
                "trainingCourse": {
                    "type": "integer"
                },
                "untilDate": {
                    "type": "string"
                },
                "updatedAt": {
                    "type": "string"
                },
                "updatedBy": {
                    "type": "integer"
                }
            },
            "example": {
                "_embedded": example_embedded_course,
                "createdAt": "2022-11-09T20:26:27.716Z",
                "date": "2022-11-09",
                "fromDate": "2022-11-09",
                "id": 1,
                "lockVersion": 1,
                "notes": None,
                "trainingCourse": 1,
                "untilDate": None,
                "updatedAt": "2022-11-09T20:26:27.716Z",
                "updatedBy": 1
            }
        }
    },
    "responses": {
        "200": {
            "description": "List of training courses",
            "schema": {
                "type": "array",
                "items": {
                    "$ref": "#/definitions/EmbeddedTrainingCourse"
                }
            }
        }
    }
}

available_trainings_schema = {
    "tags": [
        "MemberTrainingsData"
    ],
    "parameters": [
        {
            "name": "member_id",
            "in": "path",
            "type": "integer",
            "required": True
        }
    ],
    "produces": [
        TYPE_JSON
    ],
    "deprecated": False,
    "responses": {
        "200": {
            "description": "List of non-absolved available training courses",
            "schema": {
                "type": "array",
                "items": {
                    "$ref": "#/definitions/Training"
                }
            }
        }
    }
}

absolve_training_again_schema = {
    "tags": [
        "AddTraining"
    ],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "type": "object",
            "required": True,
            "schema": {
                "$ref": "#/definitions/AbsolveTrainingAgainInputs"
            }
        }
    ],
    "consumes": [
        TYPE_JSON
    ],
    "produces": [
        TYPE_JSON
    ],
    "deprecated": False,
    "definitions": {
        "AbsolveTrainingAgainInputs": {
            "type": "object",
            "required": [
                "member_id",
                "training_id"
            ],
            "properties": {
                "member_id": {
                    "type": "integer",
                    "description": "Member ID from Fabman"
                },
                "training_id": {
                    "type": "integer",
                    "description": "Training-course ID from Fabman"
                }
            },
            "example": {
                "member_id": 123456,
                "training_id": 1234
            }
        },
        "AbsolveTrainingAgainOutputs": {
            "type": "object",
            "properties": {
                "cm_url": {
                    "type": "string",
                    "description": "Full URL to ClassMarker quiz"
                }
            },
            "example": {
                "cm_url": "https://www.classmarker.com/online-test/start/?quiz=XXX&cm_user_id=encrypted<membed_id-training_id>"
            }
        }
    },
    "responses": {
        "200": {
            "description": "ClassMarker quiz URL for retaking the training",
            "schema": {
                "$ref": "#/definitions/AbsolveTrainingAgainOutputs"
            }
        }
    }
}

cm_quiz_hook_schema = {
    "tags": [
        "AddTraining"
    ],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "type": "object",
            "required": True,
            "schema": {
                "$ref": "#/definitions/CMWebhook"
            }
        }
    ],
    "externalDocs": [
        {
            "description": "ClassMarker webhook body",
            "url": "https://www.classmarker.com/online-testing/docs/webhooks/#group-results"
        }
    ],
    "produces": [
        TYPE_JSON
    ],
    "definitions": {
        "CMTest": {
            "type": "object",
            "properties": {
                "test_id": {
                    "type": "number"
                },
                "test_name": {
                    "type": "string"
                }
            },
            "example": cm_test
        },
        "CMLink": {
            "type": "object",
            "properties": {
                "link_id": {
                    "type": "number"
                },
                "link_name": {
                    "type": "string"
                },
                "link_url_id": {
                    "type": "string"
                }
            },
            "example": cm_link
        },
        "CMResult": {
            "type": "object",
            "properties": {
                "link_result_id": {
                    "type": "number"
                },
                "first": {
                    "type": "string"
                },
                "last": {
                    "type": "string"
                },
                "email": {
                    "type": "string"
                },
                "percentage": {
                    "type": "number"
                },
                "points_scored": {
                    "type": "number"
                },
                "points_available": {
                    "type": "number"
                },
                "requires_grading": {
                    "type": "string"
                },
                "time_started": {
                    "type": "number"
                },
                "time_finished": {
                    "type": "number"
                },
                "duration": {
                    "type": "string"
                },
                "percentage_passmark": {
                    "type": "string"
                },
                "passed": {
                    "type": "boolean"
                },
                "feedback": {
                    "type": "string"
                },
                "give_certificate_only_when_passed": {
                    "type": "boolean"
                },
                "certificate_url": {
                    "type": "string"
                },
                "certificate_serial": {
                    "type": "string"
                },
                "view_results_url": {
                    "type": "string"
                },
                "access_code_question": {
                    "type": "string"
                },
                "access_code_used": {
                    "type": "string"
                },
                "extra_info_question": {
                    "type": "string"
                },
                "extra_info_answer": {
                    "type": "string"
                },
                "cm_user_id": {
                    "type": "string"
                },
                "ip_address": {
                    "type": "string"
                }
            },
            "example": cm_result
        },
        "CMWebhook": {
            "type": "object",
            "properties": {
                "payload_type": {
                    "type": "string"
                },
                "payload_status": {
                    "type": "string"
                },
                "test": {
                    "$ref": "#/definitions/CMTest"
                },
                "link": {
                    "$ref": "#/definitions/CMLink"
                },
                "result": {
                    "$ref": "#/definitions/CMResult"
                }
            },
            "example": cm_hook_body
        }
    },
    "deprecated": False,
    "responses": {
        "200": {
            "description": "Success message",
            "schema": {
                "type": "string",
                "example": "Training passed, updated in Fabman"
            }
        }
    }
}

expiration_schema = {
    "tags": [
        "SchedulersRequests"
    ],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "type": "object",
            "required": True,
            "schema": {
                "$ref": "#/definitions/TrainingURLSInputs"
            }
        }
    ],
    "consumes": [
        TYPE_JSON
    ],
    "produces": [
        TYPE_JSON
    ],
    "deprecated": False,
    "definitions": {
        "TrainingURLSInputs": training_urls_inputs,
        "TrainingURLSOuputs": training_urls_outputs
    },
    "responses": {
        "200": {
            "description": "Full URL for online course",
            "schema": {
                "$ref": "#definitions/TrainingURLSOuputs"
            }
        }
    }
}

locked_booking_schema = {
    "tags": [
        "SchedulersRequests"
    ],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "type": "object",
            "required": True,
            "schema": {
                "$ref": "#/definitions/LockedBookingInputs"
            }
        }
    ],
    "consumes": [
        TYPE_JSON
    ],
    "produces": [
        TYPE_JSON
    ],
    "deprecated": False,
    "definitions": {
        "LockedBookingInputs": {
            "type": "object",
            "required": [
                "member_id",
                "member_email",
                "resource"
            ],
            "properties": {
                "member_id": {
                    "type": "integer",
                    "description": "Member ID from Fabman"
                },
                "member_email": {
                    "type": "string",
                    "description": "Email address of the member"
                },
                "resource": {
                    "type": "string",
                    "description": "Name of the locked resource"
                }
            },
            "example": {
                "member_id": 123456,
                "member_email": "user@example.com",
                "resource": "Example Resource"
            }
        }
    },
    "responses": {
        "200": {
            "description": "Notification sent successfully",
            "schema": {
                "type": "string",
                "example": ""
            }
        }
    }
}
