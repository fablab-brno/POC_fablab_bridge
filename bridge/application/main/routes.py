from flask import Response, request, jsonify, render_template

from application.services.tools import track_api_time
from ..configs import swagger_config
from . import main
from ..services.error_handlers import error_handler
from ..services.api_functions import get_list_of_available_trainings_fn, get_training_links_fn,\
    add_classmarker_training_fn, training_expiration_fn, get_list_of_absolved_trainings_fn
# locked_bookings_fn, activities_notifications_fn
from ..services.extensions import swag_from


@main.route("/health", methods=["GET"])
@error_handler
def service_healthcheck():
    """
    Service healthcheck endpoint.
    """
    return Response("", 200)

@main.route("/add_classmarker_training", methods=["POST"])
@swag_from(swagger_config.cm_quiz_hook_schema)
@error_handler
def add_classmarker_training():
    """
    Endpoint for ClassMarker webhook
    """
    return add_classmarker_training_fn(request)


@main.route("/absolved_trainings/<member_id>", methods=["GET"])
@swag_from(swagger_config.absolved_trainings_schema)
@track_api_time
@error_handler
def get_list_of_absolved_trainings(member_id: str):
    """
    List of member's active trainings
    """
    return get_list_of_absolved_trainings_fn(member_id)


@main.route("/available_trainings/<member_id>", methods=["GET"])
@swag_from(swagger_config.available_trainings_schema)
@track_api_time
@error_handler
def get_list_of_available_trainings(member_id: str):
    """
    List of all trainings available for online course
    """
    return get_list_of_available_trainings_fn(member_id)


@main.route("/get_training_links", methods=["POST"])
@swag_from(swagger_config.training_urls_schema)
@error_handler
def get_training_links():
    """
    Training's detail
    """
    return get_training_links_fn(request)


@main.route("/training_expiration", methods=["POST"])
@swag_from(swagger_config.expiration_schema)
@error_handler
def training_expiration():
    """
    Handle expiration of trainings
    """
    return training_expiration_fn(request)


# ------------------------ !!!FUTURE!!! ------------------------
# @main.route("/activities", methods=["POST"])
# @error_handler
# def activities_notifications():
#     """
#     Future functionality, event listener for disabled and re-enabled resources
#     :return: info about resource
#     """
#     # TEST EVENT
#     # {
#     #     'id': 2278519,
#     #     'type': 'test',
#     #     'createdAt': '2024-10-07T18:11:02.420Z',
#     #     'details': {
#     #         'message': 'This is a test event created by Jakub',
#     #         'createdBy': {} # member data
#     #     }
#     # }
#
#     # MACHINE ENABLED
#     # {
#     #     'id': 2278521,
#     #     'type': 'resource_updated',
#     #     'createdAt': '2024-10-07T18:14:28.417Z',
#     #     'details': {
#     #         'resource': {
#     #             'id': 4311,
#     #             'name': 'Testovací stroj pro Discord',
#     #             'type': 5641,
#     #             'debug': False,
#     #             'space': 3,
#     #             'state': 'active',
#     #             'input1': None,
#     #             'input2': None,
#     #             'account': 4,
#     #             'inputAC': None,
#     #             'metadata': None,
#     #             'createdAt': '2023-09-27T08:40:27.215Z',
#     #             'updatedAt': '2024-10-07T18:14:28.415Z',
#     #             'updatedBy': 246215,
#     #             'canBeBooked': False,
#     #             'controlType': 'machine',
#     #             'description': None,
#     #             'lockVersion': 22,
#     #             'muteDeadMan': False,
#     #             'auxEquipment': None,
#     #             'displayTitle': None,
#     #             'hasCountdown': False,
#     #             'mustBeBooked': False,
#     #             'pricePerUsage': '0.00',
#     #             'safetyMessage': None,
#     #             'stopAfterBusy': False,
#     #             'exclusiveUsage': False,
#     #             'input1Inverted': False,
#     #             'input2Inverted': False,
#     #             'inputACInverted': False,
#     #             'maxOfflineUsage': 0,
#     #             'pricePerBooking': '0.00',
#     #             'maintenanceNotes': '<div>Test toho, že flow funguje správně.</div>',
#     #             'pricePerTimeBusy': '0.00',
#     #             'pricePerTimeIdle': '0.00',
#     #             'requiresTraining': False,
#     #             'numFailedAttempts': 0,
#     #             'visibleForMembers': False,
#     #             'idlePowerThreshold': None,
#     #             'deadManIntervalBusy': 0,
#     #             'deadManIntervalIdle': 0,
#     #             'lastFailedAttemptAt': None,
#     #             'exhaustErrorShutdown': None,
#     #             'pricePerBookingSeconds': 3600,
#     #             'pricePerTimeBusySeconds': 3600,
#     #             'pricePerTimeIdleSeconds': 3600,
#     #             'preventPowerOffWhileBusy': None,
#     #             'pricingMinDurationSeconds': 0,
#     #             'bookingMaxMinutesPerMemberDay': None,
#     #             'bookingMaxMinutesPerMemberWeek': None
#     #         }
#     #     }
#     # }
#
#     # active/deactive machine
#
#     # test_data = {
#     #     'name': 'Testovací stroj pro Discord',
#     #     'state': 'locked',
#     #     'updatedBy': 246215,
#     #     'maintenanceNotes': '<div>Test toho, že flow funguje správně.</div>',
#     #     'createdAt': '2024-10-07T18:27:32.329Z',
#     #     'type': 'resource_updated',
#     #     'details': {
#     #         'resource': {
#     #             'id': 4311,
#     #             'name': 'Testovací stroj pro Discord',
#     #             'type': 5641,
#     #             'state': 'active',
#     #             'metadata': None,
#     #             'updatedAt': '2024-10-07T18:14:28.415Z',
#     #             'updatedBy': 246215,
#     #             'canBeBooked': False,
#     #             'controlType': 'machine',
#     #             'lockVersion': 22,
#     #             'maintenanceNotes': '<div>Test toho, že flow funguje správně.</div>'
#     #         }
#     #     }
#     # }
#
#     return activities_notifications_fn(request)
