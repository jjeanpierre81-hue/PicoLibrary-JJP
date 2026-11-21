"""
# Display.py
# Display view wrapper class for the CRMC system targeting a 16x2 LCD.
# Author: jjeanpierre81-hue
"""

from Log import *


class Display:
    """
    Display view class for the CRMC system that wraps an LCDDisplay to present
    customer, contact, and activity information on a 16x2 character display.

    Parameters:
    ----------
    lcd : LCDDisplay, optional
        Pre-configured LCDDisplay instance or mock display. If None, instantiates
        a new LCDDisplay using the specified I2C pins.
    sda : int, optional
        SDA pin number for I2C communication (default: 0)
    scl : int, optional
        SCL pin number for I2C communication (default: 1)
    i2c_addr : int, optional
        I2C backpack device address (default: None, auto-detected)

    Examples:
    ---------
    1. display = Display(sda=0, scl=1)
    2. display.showCustomer(customer)
    3. display.showContact(contact)
    4. display.showActivity(activity)
    5. display.clear()
    """

    def __init__(self, lcd=None, sda=0, scl=1, i2c_addr=None):
        if lcd is not None:
            self._lcd = lcd
        else:
            from Displays import LCDDisplay
            Log.i(f"Display: Initializing LCDDisplay on SDA={sda}, SCL={scl}")
            self._lcd = LCDDisplay(sda=sda, scl=scl, i2c_addr=i2c_addr)

        self._currentScreen = "IDLE"

    @property
    def lcd(self):
        """Returns the underlying LCDDisplay instance."""
        return self._lcd

    @property
    def currentScreen(self) -> str:
        """Returns the current screen identifier."""
        return self._currentScreen

    def clear(self):
        """
        Clears the LCD screen and resets the current screen state to 'CLEARED'.
        """
        Log.i("Display: clear")
        self._currentScreen = "CLEARED"
        self._lcd.clear()

    def showCustomer(self, customer):
        """
        Displays customer information across the two LCD rows.
        Row 0: Customer ID indicator (e.g. 'Cust #101')
        Row 1: Customer Name (truncated to 16 characters)

        Parameters:
        ----------
        customer : Customer or dict
            The Customer instance or dict with customer details to display
        """
        self.clear()
        self._currentScreen = "CUSTOMER"

        cid = getattr(customer, "customerID", None)
        if cid is None and isinstance(customer, dict):
            cid = customer.get("customerID", "")

        cname = getattr(customer, "customerName", None)
        if cname is None and isinstance(customer, dict):
            cname = customer.get("customerName", "")

        line1 = f"Cust #{cid}"[:16].ljust(16)
        line2 = f"{cname}"[:16].ljust(16)

        Log.i(f"Display: showCustomer -> Line 1: '{line1.strip()}' | Line 2: '{line2.strip()}'")
        self._lcd.showText(line1, row=0, col=0)
        self._lcd.showText(line2, row=1, col=0)

    def showContact(self, contact):
        """
        Displays contact information across the two LCD rows.
        Row 0: Contact Name (truncated to 16 characters)
        Row 1: Contact Role (truncated to 16 characters)

        Parameters:
        ----------
        contact : Contact or dict
            The Contact instance or dict with contact details to display
        """
        self.clear()
        self._currentScreen = "CONTACT"

        cname = getattr(contact, "contactName", None)
        if cname is None and isinstance(contact, dict):
            cname = contact.get("contactName", "")

        crole = getattr(contact, "contactRole", None)
        if crole is None and isinstance(contact, dict):
            crole = contact.get("contactRole", "")

        line1 = f"{cname}"[:16].ljust(16)
        line2 = f"Role: {crole}"[:16].ljust(16)

        Log.i(f"Display: showContact -> Line 1: '{line1.strip()}' | Line 2: '{line2.strip()}'")
        self._lcd.showText(line1, row=0, col=0)
        self._lcd.showText(line2, row=1, col=0)

    def showActivity(self, activity):
        """
        Displays activity information across the two LCD rows.
        Row 0: Activity Type and Date (truncated to 16 characters)
        Row 1: Activity Description (truncated to 16 characters)

        Parameters:
        ----------
        activity : Activity or dict
            The Activity instance or dict with activity details to display
        """
        self.clear()
        self._currentScreen = "ACTIVITY"

        atype = getattr(activity, "activityType", None)
        if atype is None and isinstance(activity, dict):
            atype = activity.get("activityType", "")

        adate = getattr(activity, "activityDate", None)
        if adate is None and isinstance(activity, dict):
            adate = activity.get("activityDate", "")

        adesc = getattr(activity, "activityDescription", None)
        if adesc is None and isinstance(activity, dict):
            adesc = activity.get("activityDescription", "")

        line1 = f"{atype}: {adate}"[:16].ljust(16)
        line2 = f"{adesc}"[:16].ljust(16)

        Log.i(f"Display: showActivity -> Line 1: '{line1.strip()}' | Line 2: '{line2.strip()}'")
        self._lcd.showText(line1, row=0, col=0)
        self._lcd.showText(line2, row=1, col=0)


if __name__ == "__main__":
    Log.i("Testing Display class with MockLCD...")

    class MockLCD:
        """Hardware-independent mock for LCDDisplay verification."""
        def __init__(self):
            self.lines = [" " * 16, " " * 16]
            self.cleared = False

        def clear(self, line=-1):
            self.cleared = True
            if line < 0 or line > 1:
                self.lines = [" " * 16, " " * 16]
            else:
                self.lines[line] = " " * 16

        def reset(self):
            self.clear()

        def showText(self, text, row=0, col=0):
            current = list(self.lines[row])
            for i, ch in enumerate(text):
                if col + i < 16:
                    current[col + i] = ch
            self.lines[row] = "".join(current)

    from Customer import Customer
    from Contact import Contact
    from Activity import Activity

    mock_lcd = MockLCD()
    disp = Display(lcd=mock_lcd)
    assert disp.currentScreen == "IDLE"

    # Test Customer rendering
    cust = Customer(101, "Wayne Enterprises")
    disp.showCustomer(cust)
    assert disp.currentScreen == "CUSTOMER"
    assert "Cust #101" in mock_lcd.lines[0]
    assert "Wayne Enterprise" in mock_lcd.lines[1]

    # Test Contact rendering
    contact = Contact(1, 101, "Lucius Fox", "Director")
    disp.showContact(contact)
    assert disp.currentScreen == "CONTACT"
    assert "Lucius Fox" in mock_lcd.lines[0]
    assert "Role: Director" in mock_lcd.lines[1]

    # Test Activity rendering
    act = Activity(1, 101, "Phone Call", "2026-11-18", "Contract review")
    disp.showActivity(act)
    assert disp.currentScreen == "ACTIVITY"
    assert "Phone Call" in mock_lcd.lines[0]
    assert "Contract review" in mock_lcd.lines[1]

    # Test Clear
    disp.clear()
    assert disp.currentScreen == "CLEARED"
    assert mock_lcd.lines[0].strip() == ""
    assert mock_lcd.lines[1].strip() == ""

    Log.i("Testing complete - all checks passed")
