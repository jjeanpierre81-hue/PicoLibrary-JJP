"""
# Contact.py
# Contact domain entity class for the CRMC system.
# Author: jjeanpierre81-hue
"""

from Log import *


class Contact:
    """
    Contact entity class representing an individual contact for a customer in the CRMC system.

    Parameters:
    ----------
    contactID : int
        Unique identifier for the contact
    customerID : int
        Identifier of the customer this contact belongs to
    contactName : str
        Full name of the contact person
    contactRole : str
        Job title or role of the contact (e.g. 'Manager', 'Lead Tech')

    Examples:
    ---------
    1. contact = Contact(1, 101, "Bruce Wayne", "CEO")
    2. details = contact.getDetails()
    """

    def __init__(self, contactID: int, customerID: int, contactName: str, contactRole: str):
        self._contactID = int(contactID)
        self._customerID = int(customerID)
        self._contactName = str(contactName)
        self._contactRole = str(contactRole)

    @property
    def contactID(self) -> int:
        """Returns the contact ID."""
        return self._contactID

    @property
    def customerID(self) -> int:
        """Returns the customer ID associated with this contact."""
        return self._customerID

    @property
    def contactName(self) -> str:
        """Returns the contact name."""
        return self._contactName

    @property
    def contactRole(self) -> str:
        """Returns the contact role."""
        return self._contactRole

    def getDetails(self) -> dict:
        """
        Return a dictionary of the contact's details.

        Returns:
        -------
        dict
            Dictionary containing contactID, customerID, contactName, and contactRole
        """
        return {
            "contactID": self._contactID,
            "customerID": self._customerID,
            "contactName": self._contactName,
            "contactRole": self._contactRole
        }

    def __str__(self) -> str:
        return f"Contact(ID={self._contactID}, CustomerID={self._customerID}, Name='{self._contactName}', Role='{self._contactRole}')"

    def __repr__(self) -> str:
        return self.__str__()


if __name__ == "__main__":
    Log.i("Testing Contact class...")
    contact = Contact(1, 101, "Lucius Fox", "Director of Technology")
    assert contact.contactID == 1
    assert contact.customerID == 101
    assert contact.contactName == "Lucius Fox"
    assert contact.contactRole == "Director of Technology"

    details = contact.getDetails()
    assert details["contactID"] == 1
    assert details["contactRole"] == "Director of Technology"
    Log.i(f"Contact details: {details}")

    Log.i("Testing complete - all checks passed")
