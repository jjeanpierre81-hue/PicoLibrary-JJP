"""
# Customer.py
# Customer domain entity class for the CRMC system.
# Author: jjeanpierre81-hue
"""

from Log import *


class Customer:
    """
    Customer entity class representing a client in the CRMC system.

    Parameters:
    ----------
    customerID : int
        Unique identifier for the customer
    customerName : str
        Full name or business title of the customer

    Examples:
    ---------
    1. cust = Customer(1, "Acme Corp")
    2. details = cust.getDetails()
    """

    def __init__(self, customerID: int, customerName: str):
        self._customerID = int(customerID)
        self._customerName = str(customerName)
        self._contacts = []
        self._activities = []

    @property
    def customerID(self) -> int:
        """Returns the customer ID."""
        return self._customerID

    @property
    def customerName(self) -> str:
        """Returns the customer name."""
        return self._customerName

    @property
    def contacts(self) -> list:
        """Returns the list of associated Contact entities."""
        return self._contacts

    @property
    def activities(self) -> list:
        """Returns the list of associated Activity entities."""
        return self._activities

    def addContact(self, contact):
        """
        Associate a Contact entity with this Customer.

        Parameters:
        ----------
        contact : Contact
            Contact instance associated with this customer
        """
        self._contacts.append(contact)

    def addActivity(self, activity):
        """
        Associate an Activity entity with this Customer.

        Parameters:
        ----------
        activity : Activity
            Activity instance associated with this customer
        """
        self._activities.append(activity)

    def getDetails(self) -> dict:
        """
        Return a dictionary of the customer's details including ID, name,
        and associated contacts and activities.

        Returns:
        -------
        dict
            Dictionary containing customerID, customerName, contacts, and activities
        """
        return {
            "customerID": self._customerID,
            "customerName": self._customerName,
            "contacts": [c.getDetails() if hasattr(c, "getDetails") else c for c in self._contacts],
            "activities": [a.getDetails() if hasattr(a, "getDetails") else a for a in self._activities]
        }

    def __str__(self) -> str:
        return f"Customer(ID={self._customerID}, Name='{self._customerName}')"

    def __repr__(self) -> str:
        return self.__str__()


if __name__ == "__main__":
    Log.i("Testing Customer class...")
    customer = Customer(101, "Wayne Enterprises")
    assert customer.customerID == 101
    assert customer.customerName == "Wayne Enterprises"

    details = customer.getDetails()
    assert details["customerID"] == 101
    assert details["customerName"] == "Wayne Enterprises"
    Log.i(f"Customer details: {details}")

    Log.i("Testing complete - all checks passed")
