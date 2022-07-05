# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from logging import exception
from typing import Any, Text, Dict, List
from xmlrpc.client import Boolean

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, AllSlotsReset, ActiveLoop, FollowupAction
from rasa_sdk.forms import FormValidationAction, REQUESTED_SLOT

import re
import pymongo
from sqlalchemy import false, true

# Mongo DB
conn_str = "mongodb+srv://kesu:keshab123@cluster0.bqo0o.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(conn_str)


class ValidateEmployeeRegisterForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_employee_register_form"

    def checkStop(self,intent) -> Boolean:
        # print(intent)
        if(intent == "Get_employee_data_by_id" or intent == "stop" or intent == "goodbye"):
            return true
        else:
            return false
    async def validate_employee_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(slot_value)
        intent = tracker.get_intent_of_latest_message()
        if self.checkStop(intent) == true:
            return {"requested_slot": None}
        elif re.search("^[A-Za-z ]+$", slot_value):
            return {"employee_name": slot_value}
        else:
            dispatcher.utter_message(
                text="Employee name should only contain Alphabets."
            )
            return {"employee_name": None}

    async def validate_employee_id(
        self,
        slot_value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        slot_value = slot_value.strip()
        print(slot_value)
        intent = tracker.get_intent_of_latest_message()
        if self.checkStop(intent) == true:
            return {"requested_slot": None}
        elif len(slot_value) == 6 and slot_value.isnumeric():
            db_name = "employee_db"
            col_name = "Employees_Info"

            my_db = client[db_name]
            my_coll = my_db[col_name]

            res = my_coll.find_one({"employee_id": slot_value})
            # print(res)
            if res == None:
                return {"employee_id": slot_value}
            else:
                dispatcher.utter_message(text="This employee ID number already exixts.")
                return {"employee_id": None}
        else:
            dispatcher.utter_message(
                text="Employee Id number should be six digit number only."
            )
            return {"employee_id": None}

    async def validate_designation(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(slot_value)
        intent = tracker.get_intent_of_latest_message()
        if self.checkStop(intent) == true:
            return {"requested_slot": None}
        elif re.search("^[A-Za-z]+[A-Za-z 0-9]*$", slot_value):
            return {"designation": slot_value}
        else:
            dispatcher.utter_message(
                text="Designation should only contain Alphabets and Numbers."
            )
            return {"designation": None}

    def validate_base_location(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        print(slot_value)
        intent = tracker.get_intent_of_latest_message()
        if self.checkStop(intent) == true:
            return {"requested_slot": None}
        elif re.search("^[A-Za-z ]+$", slot_value):
            return {"base_location": slot_value}
        else:
            dispatcher.utter_message(
                text="Base location should only contain Alphabets."
            )
            return {"base_location": None}


class SubmitEmployeeRegisterForm(Action):
    def name(self) -> Text:
        return "submit_employee_register_form"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:
        intent = tracker.get_intent_of_latest_message()
        if intent == "stop" or intent == "goodbye":
            dispatcher.utter_message(response="utter_form_stopped")
            dispatcher.utter_message(response="utter_what_else_CanIDoForYou")
            return [ActiveLoop(None), SlotSet(REQUESTED_SLOT, None), AllSlotsReset()]
        elif intent == "Get_employee_data_by_id":
            # dispatcher.utter_message(response="utter_fill_form_all_details")
            q_emp_id = tracker.get_slot("q_employee_id")
            print(q_emp_id)
            return [ActiveLoop("employee_query_form"), AllSlotsReset(), FollowupAction(name="employee_query_form")]
        else:
            try:
                emp_id = tracker.get_slot("employee_id")
                emp_name = tracker.get_slot("employee_name")
                desig = tracker.get_slot("designation")
                base_loc = tracker.get_slot("base_location")

                emp_dict = {
                    "employee_id": emp_id,
                    "employee_name": emp_name,
                    "designation": desig,
                    "base_location": base_loc,
                }

                db_name = "employee_db"
                col_name = "Employees_Info"

                my_db = client[db_name]
                my_coll = my_db[col_name]

                # if(emp_id==null and )
                res = my_coll.insert_one(emp_dict)
                # print(f"Submit res type: {res.acknowledged} : {type(res.acknowledged)}")
                if res.acknowledged == True:
                    emp_details = {
                        "payload": "infoCard",
                        "data": [
                            {
                                "title": "Employee Details:",
                                "name": emp_name,
                                "id": emp_id,
                                "role": desig,
                                "location": base_loc,
                            },
                        ],
                    }
                    print("response sent")
                    dispatcher.utter_message(
                        response="utter_employee_register_form_submitted"
                    )
                    dispatcher.utter_message(json_message= emp_details)
                    dispatcher.utter_message(response="utter_what_else_CanIDoForYou")
                    return [AllSlotsReset()]
                else:
                    return [AllSlotsReset(), FollowupAction(name="utter_cant_register")]

            except Exception:
                print("Unable to connect to the server.")
                intent = tracker.get_intent_of_latest_message()
                print(f"Intent was: {intent}")
                dispatcher.utter_message(
                    text="Cannot insert data to Database.Please try again."
                )
                return [AllSlotsReset()]


class SubmitEmployeeQueryForm(Action):
    def name(self) -> Text:
        return "submit_employee_query_form"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:
        q_emp_id = tracker.get_slot("q_employee_id")
        intent = tracker.get_intent_of_latest_message()
        if intent == "stop" or intent == "goodbye":
            dispatcher.utter_message(response="utter_form_stopped")
            dispatcher.utter_message(response="utter_what_else_CanIDoForYou")
            return [ActiveLoop(None), SlotSet(REQUESTED_SLOT, None), AllSlotsReset()]
        elif intent == "Register_employee":
            dispatcher.utter_message(response="utter_fill_form_all_details")
            return [ActiveLoop("employee_register_form"), AllSlotsReset(), FollowupAction(name="employee_register_form")]
        elif re.search("^[0-9]{6}$", q_emp_id):
            try:
                # print("Details are")
                db_name = "employee_db"
                col_name = "Employees_Info"

                my_db = client[db_name]
                my_coll = my_db[col_name]

                my_query = {"employee_id": q_emp_id}
                res = my_coll.find_one(my_query)
                if res != None:
                    print("found")
                    emp_name = res["employee_name"]
                    emp_id = res["employee_id"]
                    emp_desg = res["designation"]
                    emp_loc = res["base_location"]
                    emp_details = {
                        "payload": "infoCard",
                        "data": [
                            {
                                "title": "Employee Details:",
                                "name": emp_name,
                                "id": emp_id,
                                "role": emp_desg,
                                "location": emp_loc,
                            },
                        ],
                    }
                    print("response sent")
                    dispatcher.utter_message(json_message= emp_details)
                    # dispatcher.utter_message(
                    #     response="utter_show_emp_details",
                    #     employee_name=emp_name,
                    #     employee_id=emp_id,
                    #     designation=emp_desg,
                    #     base_location=emp_loc,
                    # )
                    dispatcher.utter_message(response="utter_what_else_CanIDoForYou")
                    return [AllSlotsReset()]
                else:
                    dispatcher.utter_message(text="This Employee ID could not be found on our database!")
                    return [ActiveLoop("employee_query_form"), AllSlotsReset()]
            except Exception:
                dispatcher.utter_message(text="Can't find any details now. Try again.")
                return [AllSlotsReset()]
        else:
            dispatcher.utter_message(text="The Employee ID is Invalid.")
            return [ActiveLoop("employee_query_form"), AllSlotsReset()]


class SubmitEmployeeDeleteForm(Action):
    def name(self) -> Text:
        return "submit_employee_delete_form"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:
        d_emp_id = tracker.get_slot("d_employee_id")
        intent = tracker.get_intent_of_latest_message()
        if intent == "stop" or intent == "goodbye":
            dispatcher.utter_message(response="utter_form_stopped")
            dispatcher.utter_message(response="utter_what_else_CanIDoForYou")
            return [ActiveLoop(None), SlotSet(REQUESTED_SLOT, None), AllSlotsReset()]
        elif re.search("^[0-9]{6}$", d_emp_id):
            try:
                # Delete entry from MongoDB
                db_name = "employee_db"
                col_name = "Employees_Info"

                my_db = client[db_name]
                my_coll = my_db[col_name]

                my_query = {"employee_id": d_emp_id}
                res = my_coll.delete_one(my_query)
                if res.deleted_count > 0:
                    print(f"Deleted : {d_emp_id}")
                    dispatcher.utter_message(
                        text=f"The details of Employee '{d_emp_id}' deleted successfully."
                    )
                    dispatcher.utter_message(response="utter_what_else_CanIDoForYou")
                    return [AllSlotsReset()]
                else:
                    dispatcher.utter_message(text="The Employee ID could not be found!")
                    return [ActiveLoop("employee_delete_form"), AllSlotsReset()]
            except Exception:
                dispatcher.utter_message(text="Can't delete employee now. Try again.")
                return [AllSlotsReset()]
        else:
            dispatcher.utter_message(text="The Employee ID is Invalid!")
            return [ActiveLoop("employee_delete_form"), AllSlotsReset()]


class ActionResourcesList(Action):
    def name(self) -> Text:
        return "action_resources_list"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        data = {
            "payload": "cardsCarousel",
            "data": [
                {
                    "image": "https://b.zmtcdn.com/data/pictures/1/18602861/bd2825ec26c21ebdc945edb7df3b0d99.jpg",
                    "title": "Taftoon Bar & Kitchen",
                    "ratings": "4.5",
                },
                {
                    "image": "https://b.zmtcdn.com/data/pictures/4/18357374/661d0edd484343c669da600a272e2256.jpg",
                    "ratings": "4.0",
                    "title": "Veranda",
                },
                {
                    "image": "https://b.zmtcdn.com/data/pictures/4/18902194/e92e2a3d4b5c6e25fd4211d06b9a909e.jpg",
                    "ratings": "4.0",
                    "title": "145 The Mill",
                },
                {
                    "image": "https://b.zmtcdn.com/data/pictures/3/17871363/c53db6ba261c3e2d4db1afc47ec3eeb0.jpg",
                    "ratings": "4.0",
                    "title": "The Fatty Bao",
                },
            ],
        }

        dispatcher.utter_message(json_message=data)
        # covid_resources = {
        #         "payload": "cardsCarousel",
        #         "data": [
        #             {
        #                 "title": "MBMC",
        #                 # "subtitle": "FIND BED, SAVE LIFE.",
        #                 "image": "static/hospital-beds-application.jpg",
        #                 # "buttons": [
        #                 #     {
        #                 #         "title": "Hospital Beds Availability",
        #                 #         "url": "https://www.covidbedmbmc.in/",
        #                 #         "type": "web_url",
        #                 #     },
        #                 #     {"title": "MBMC", "type": "postback", "payload": "/affirm"},
        #                 # ],
        #             },
        #             {
        #                 "title": "COVID.ARMY",
        #                 # "subtitle": "OUR NATION, SAVE NATION.",
        #                 "image": "static/oxygen-cylinder-55-cft-500x554-500x500.jpg",
        #                 # "buttons": [
        #                 #     {
        #                 #         "title": "RESOURCES AVAILABILITY",
        #                 #         "url": "https://covid.army/",
        #                 #         "type": "web_url",
        #                 #     },
        #                 #     {
        #                 #         "title": "COVID ARMY",
        #                 #         "type": "postback",
        #                 #         "payload": "/deny",
        #                 #     },
        #                 # ],
        #             },
        #             {
        #                 "title": "Innovate Youself",
        #                 # "subtitle": "Get It, Make it.",
        #                 "image": "static/test.jpg",
        #                 # "buttons": [
        #                 #     {
        #                 #         "title": "Innovate Yourself",
        #                 #         "url": "https://www.innovationyourself.com/",
        #                 #         "type": "web_url",
        #                 #     },
        #                 #     {
        #                 #         "title": "Innovate Yourself",
        #                 #         "type": "postback",
        #                 #         "payload": "/greet",
        #                 #     },
        #                 # ],
        #             },
        #             {
        #                 "title": "RASA CHATBOT",
        #                 # "subtitle": "Conversational AI",
        #                 "image": "static/rasa.png",
        #                 # "buttons": [
        #                 #     {
        #                 #         "title": "Rasa",
        #                 #         "url": "https://www.rasa.com",
        #                 #         "type": "web_url",
        #                 #     },
        #                 #     {
        #                 #         "title": "Rasa Chatbot",
        #                 #         "type": "postback",
        #                 #         "payload": "/greet",
        #                 #     },
        #                 # ],
        #             },
        #         ],
        #     },

        # dispatcher.utter_message(json_message=covid_resources)
        return []
