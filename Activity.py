"""
# Activity.py
# Activity domain entity class for the CRMC system.
# Author: jjeanpierre81-hue
"""

from Log import *


class Activity:
    """
    Activity entity class representing an interaction or log entry for a customer in the CRMC system.

    Parameters:
    ----------
    activityID : int
        Unique identifier for the activity record
    customerID : int
        Identifier of the customer associated with this activity
    activityType : str
        Type of activity (e.g. 'Call', 'Meeting', 'Email', 'Note')
    activityDate : str
        Date of the activity (e.g. '2026-11-18')
    activityDescription : str
        Summary or narrative description of the activity

    Examples:
    ---------
    1. activity = Activity(1, 101, "Meeting", "2026-11-18", "Quarterly review")
    2. details = activity.getDetails()
    """

    def __init__(self, activityID: int, customerID: int, activityType: str, activityDate: str, activityDescription: str):
        self._activityID = int(activityID)
        self._customerID = int(customerID)
        self._activityType = str(activityType)
        self._activityDate = str(activityDate)
        self._activityDescription = str(activityDescription)

    @property
    def activityID(self) -> int:
        """Returns the activity ID."""
        return self._activityID

    @property
    def customerID(self) -> int:
        """Returns the customer ID associated with this activity."""
        return self._customerID

    @property
    def activityType(self) -> str:
        """Returns the activity type."""
        return self._activityType

    @property
    def activityDate(self) -> str:
        """Returns the date of the activity."""
        return self._activityDate

    @property
    def activityDescription(self) -> str:
        """Returns the description of the activity."""
        return self._activityDescription

    def getDetails(self) -> dict:
        """
        Return a dictionary of the activity's details.

        Returns:
        -------
        dict
            Dictionary containing activityID, customerID, activityType, activityDate, and activityDescription
        """
        return {
            "activityID": self._activityID,
            "customerID": self._customerID,
            "activityType": self._activityType,
            "activityDate": self._activityDate,
            "activityDescription": self._activityDescription
        }

    def __str__(self) -> str:
        return f"Activity(ID={self._activityID}, CustomerID={self._customerID}, Type='{self._activityType}', Date='{self._activityDate}')"

    def __repr__(self) -> str:
        return self.__str__()


if __name__ == "__main__":
    Log.i("Testing Activity class...")
    act = Activity(1, 101, "Phone Call", "2026-11-18", "Discussed project deliverables")
    assert act.activityID == 1
    assert act.customerID == 101
    assert act.activityType == "Phone Call"
    assert act.activityDate == "2026-11-18"
    assert act.activityDescription == "Discussed project deliverables"

    details = act.getDetails()
    assert details["activityID"] == 1
    assert details["activityType"] == "Phone Call"
    Log.i(f"Activity details: {details}")

    Log.i("Testing complete - all checks passed")
