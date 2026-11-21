"""
# CRMCController.py
# Main controller for the CRMC system orchestrating Network, Button, Display, and domain models.
# Author: jjeanpierre81-hue
"""

import time
from Log import *
from Customer import Customer
from Contact import Contact
from Activity import Activity


class CRMCController:
    """
    CRMCController coordinates network API communication, user input from a push button,
    16x2 LCD display updates, and customer domain models.

    Supports both Sequence A (Eager bulk loading) and Sequence B (Lazy on-demand loading).

    Parameters:
    ----------
    net : Net, optional
        Network adapter instance. If None, lazily instantiated from Net.py.
    button : Button, optional
        Button instance for interaction. If None, lazily instantiated from Button.py.
    display : Display, optional
        Display view wrapper instance. If None, lazily instantiated from Display.py.
    base_url : str, optional
        Base URL for the Customers API (default: "")
    ssid : str, optional
        Wi-Fi network SSID (default: "")
    password : str, optional
        Wi-Fi network password (default: None)
    mode : str, optional
        Data loading strategy: 'A' for eager loading or 'B' for lazy loading (default: 'B')
    button_pin : int, optional
        GPIO pin number for the hardware button if instantiated automatically (default: 14)

    Examples:
    ---------
    1. controller = CRMCController(base_url="http://192.168.1.100:5000", mode="B")
    2. controller.start()
    3. controller.handleButton()
    """

    # View sub-states for rotating through details on 16x2 LCD
    VIEW_CUSTOMER = 0
    VIEW_CONTACT = 1
    VIEW_ACTIVITY = 2

    def __init__(self, net=None, button=None, display=None, base_url="", ssid="", password=None, mode="B", button_pin=14):
        self._net = net
        self._button = button
        self._display = display
        self._base_url = base_url.rstrip("/") if base_url else ""
        self._ssid = ssid
        self._password = password
        self._mode = mode.upper() if mode else "B"
        self._button_pin = button_pin

        # Data stores
        self._customers = []
        self._all_contacts = []
        self._all_activities = []

        # Navigation state
        self._current_customer_index = 0
        self._selected_customer_id = None
        self._current_view_state = self.VIEW_CUSTOMER
        self._current_contact_index = 0
        self._current_activity_index = 0

        # Interrupt safety state
        self._button_pending = False
        self._last_button_time = 0

        Log.i(f"CRMCController: Initialized in Mode {self._mode} with Base URL '{self._base_url}'")

    @property
    def net(self):
        """Returns the Net instance, lazily importing and initializing if necessary."""
        if self._net is None:
            try:
                from Net import Net
                self._net = Net()
            except ImportError as e:
                Log.e(f"CRMCController: Could not import Net ({e})")
        return self._net

    @property
    def button(self):
        """Returns the Button instance, lazily importing and initializing if necessary."""
        if self._button is None:
            try:
                from Button import Button
                self._button = Button(self._button_pin, "CRMC_Button", handler=self)
            except ImportError as e:
                Log.e(f"CRMCController: Could not import Button ({e})")
        return self._button

    @property
    def display(self):
        """Returns the Display instance, lazily importing and initializing if necessary."""
        if self._display is None:
            try:
                from Display import Display
                self._display = Display()
            except ImportError as e:
                Log.e(f"CRMCController: Could not import Display ({e})")
        return self._display

    @property
    def customers(self) -> list:
        """Returns the list of loaded Customer entities."""
        return self._customers

    @property
    def all_contacts(self) -> list:
        """Returns the list of all cached Contact entities (Sequence A)."""
        return self._all_contacts

    @property
    def all_activities(self) -> list:
        """Returns the list of all cached Activity entities (Sequence A)."""
        return self._all_activities

    @property
    def currentCustomer(self):
        """Returns the currently active Customer instance, or None if none loaded."""
        if self._customers and 0 <= self._current_customer_index < len(self._customers):
            return self._customers[self._current_customer_index]
        return None

    # -------------------------------------------------------------------------
    # UML Core Methods
    # -------------------------------------------------------------------------

    def start(self):
        """
        Starts the CRMC controller. Connects to network, verifies local IP,
        queries API version, and triggers initial data loading according to mode.
        """
        Log.i("CRMCController: Starting system...")

        # 1. Connect to Wi-Fi if credentials supplied and not already connected
        net_instance = self.net
        if net_instance is not None:
            # Provide diagram method alias if Net only has getLocalIp
            if hasattr(net_instance, "getLocalIp") and not hasattr(net_instance, "getlocalip"):
                net_instance.getlocalip = net_instance.getLocalIp

            if self._ssid:
                try:
                    Log.i(f"CRMCController: Connecting to Wi-Fi SSID '{self._ssid}'...")
                    net_instance.connect(self._ssid, self._password)
                except Exception as e:
                    Log.e(f"CRMCController: Network connection error: {e}")

            # Verify local IP
            ip = "Unknown"
            if hasattr(net_instance, "getlocalip"):
                ip = net_instance.getlocalip()
            elif hasattr(net_instance, "getLocalIp"):
                ip = net_instance.getLocalIp()
            Log.i(f"CRMCController: Local IP Address: {ip}")

            # Query API Version (Sequence A & B step: getJson(URL='version'))
            version_url = self._build_url("version")
            try:
                ver_resp = net_instance.getJson(version_url)
                Log.i(f"CRMCController: Customers API Version Response: {ver_resp}")
            except Exception as e:
                Log.w(f"CRMCController: Could not fetch API version ({e})")

        # 2. Attach button handler
        btn = self.button
        if btn is not None and hasattr(btn, "setHandler"):
            btn.setHandler(self)

        # 3. Load data according to selected sequence mode
        if self._mode == "A":
            Log.i("CRMCController: Running Sequence A (Eager Loading)...")
            self.loadAllDetails()
        else:
            Log.i("CRMCController: Running Sequence B (Lazy Loading)...")
            self.loadCustomers()

        # 4. Display initial customer list
        if self._customers:
            self.selectCustomer(self._customers[0].customerID)
        else:
            self.updateDisplay()

    def loadCustomers(self) -> list:
        """
        Fetches the customer list from the Customers API ('/customer/get_customers').
        Converts results into Customer instances and updates internal state.

        Returns:
        -------
        list
            List of loaded Customer instances
        """
        url = self._build_url("get_customers")
        Log.i(f"CRMCController: Fetching customers from {url}...")
        raw_data = self._fetch_json(url)

        records = self._extract_list(raw_data, "customers")
        self._customers = []
        for item in records:
            cust = self._parse_customer(item)
            if cust:
                self._customers.append(cust)

        Log.i(f"CRMCController: Successfully loaded {len(self._customers)} customers")
        return self._customers

    def loadAllDetails(self):
        """
        Sequence Diagram A (Eager Loading): Fetches all customers, all contacts,
        and all activities upfront, linking them together in memory.
        """
        Log.i("CRMCController: loadAllDetails - Initiating bulk eager fetch...")

        # 1. Fetch all customers
        self.loadCustomers()

        # 2. Fetch all contacts (GET /contacts)
        contacts_url = self._build_url("contacts")
        Log.i(f"CRMCController: Fetching all contacts from {contacts_url}...")
        raw_contacts = self._fetch_json(contacts_url)
        contact_records = self._extract_list(raw_contacts, "contacts")

        self._all_contacts = []
        for item in contact_records:
            cnt = self._parse_contact(item)
            if cnt:
                self._all_contacts.append(cnt)

        # 3. Fetch all activities (GET /activities)
        activities_url = self._build_url("activities")
        Log.i(f"CRMCController: Fetching all activities from {activities_url}...")
        raw_activities = self._fetch_json(activities_url)
        activity_records = self._extract_list(raw_activities, "activities")

        self._all_activities = []
        for item in activity_records:
            act = self._parse_activity(item)
            if act:
                self._all_activities.append(act)

        # 4. Associate contacts and activities to corresponding customers
        cust_map = {c.customerID: c for c in self._customers}
        for cnt in self._all_contacts:
            if cnt.customerID in cust_map:
                cust_map[cnt.customerID].addContact(cnt)

        for act in self._all_activities:
            if act.customerID in cust_map:
                cust_map[act.customerID].addActivity(act)

        Log.i(f"CRMCController: Bulk load complete. Customers: {len(self._customers)}, Contacts: {len(self._all_contacts)}, Activities: {len(self._all_activities)}")

    def selectCustomer(self, customerID: int):
        """
        Selects an active customer by customerID and loads or filters associated data.

        In Mode A: Calls filterNonClientData(customerID) to filter pre-fetched data.
        In Mode B: Calls loadContacts(customerID) and loadActivities(customerID) on demand.

        Parameters:
        ----------
        customerID : int
            Identifier of the customer to select
        """
        Log.i(f"CRMCController: selectCustomer({customerID})")
        self._selected_customer_id = customerID

        # Find customer index in local list
        for idx, c in enumerate(self._customers):
            if c.customerID == customerID:
                self._current_customer_index = idx
                break

        cust = self.currentCustomer

        if self._mode == "A":
            # Sequence Diagram A: filter pre-fetched bulk data
            filtered_contacts, filtered_activities = self.filterNonClientData(customerID)
            Log.i(f"CRMCController: (Mode A) Filtered {len(filtered_contacts)} contacts and {len(filtered_activities)} activities for Customer {customerID}")
        else:
            # Sequence Diagram B: query on-demand
            Log.i(f"CRMCController: (Mode B) Loading on-demand details for Customer {customerID}...")
            self.loadContacts(customerID)
            self.loadActivities(customerID)

        # Reset view rotation back to customer summary
        self._current_view_state = self.VIEW_CUSTOMER
        self._current_contact_index = 0
        self._current_activity_index = 0

        self.updateDisplay()

    def loadContacts(self, customerID: int) -> list:
        """
        Sequence Diagram B (Lazy Loading): Queries API for contacts belonging
        to a specific customer ('/contacts?customerID=<id>').

        Parameters:
        ----------
        customerID : int
            Customer identifier

        Returns:
        -------
        list
            List of Contact instances
        """
        url = self._build_url("contacts", customerID=customerID)
        Log.i(f"CRMCController: Fetching contacts for Customer {customerID} from {url}...")
        raw_data = self._fetch_json(url)

        records = self._extract_list(raw_data, "contacts")
        loaded_contacts = []
        for item in records:
            cnt = self._parse_contact(item, default_cid=customerID)
            if cnt:
                loaded_contacts.append(cnt)

        # Associate with current customer if matching
        cust = self.currentCustomer
        if cust and cust.customerID == customerID:
            # Avoid duplicate references if re-polled
            existing_ids = {c.contactID for c in cust.contacts}
            for cnt in loaded_contacts:
                if cnt.contactID not in existing_ids:
                    cust.addContact(cnt)

        return loaded_contacts

    def loadActivities(self, customerID: int) -> list:
        """
        Sequence Diagram B (Lazy Loading): Queries API for activities belonging
        to a specific customer ('/activities?customerID=<id>').

        Parameters:
        ----------
        customerID : int
            Customer identifier

        Returns:
        -------
        list
            List of Activity instances
        """
        url = self._build_url("activities", customerID=customerID)
        Log.i(f"CRMCController: Fetching activities for Customer {customerID} from {url}...")
        raw_data = self._fetch_json(url)

        records = self._extract_list(raw_data, "activities")
        loaded_activities = []
        for item in records:
            act = self._parse_activity(item, default_cid=customerID)
            if act:
                loaded_activities.append(act)

        # Associate with current customer if matching
        cust = self.currentCustomer
        if cust and cust.customerID == customerID:
            existing_ids = {a.activityID for a in cust.activities}
            for act in loaded_activities:
                if act.activityID not in existing_ids:
                    cust.addActivity(act)

        return loaded_activities

    def filterNonClientData(self, customerID: int) -> tuple:
        """
        Sequence Diagram A (Step 9.1): Filters cached contacts and activities
        belonging specifically to customerID.

        Parameters:
        ----------
        customerID : int
            Customer identifier

        Returns:
        -------
        tuple
            (filtered_contacts, filtered_activities)
        """
        filtered_contacts = [c for c in self._all_contacts if c.customerID == customerID]
        filtered_activities = [a for a in self._all_activities if a.customerID == customerID]
        return (filtered_contacts, filtered_activities)

    def handleButton(self):
        """
        Advances the interaction state upon a button press:
        - If viewing Customer and customer has contacts -> shows Contact.
        - If viewing Contact and customer has activities -> shows Activity.
        - Otherwise -> cycles to the next Customer in the list.
        """
        if not self._customers:
            Log.w("CRMCController: handleButton called but no customers loaded.")
            return

        cust = self.currentCustomer
        if not cust:
            return

        if self._current_view_state == self.VIEW_CUSTOMER:
            if cust.contacts:
                self._current_view_state = self.VIEW_CONTACT
                self._current_contact_index = 0
                self.updateDisplay()
                return
            elif cust.activities:
                self._current_view_state = self.VIEW_ACTIVITY
                self._current_activity_index = 0
                self.updateDisplay()
                return

        elif self._current_view_state == self.VIEW_CONTACT:
            if cust.activities:
                self._current_view_state = self.VIEW_ACTIVITY
                self._current_activity_index = 0
                self.updateDisplay()
                return

        # Advance to next customer
        self._current_customer_index = (self._current_customer_index + 1) % len(self._customers)
        next_cust = self._customers[self._current_customer_index]
        self.selectCustomer(next_cust.customerID)

    def updateDisplay(self):
        """
        Updates the 16x2 LCD display by delegating to Display methods:
        - showCustomer() when on customer summary screen
        - showContact() when viewing contact details
        - showActivity() when viewing activity details
        - clear() if no data is available
        """
        disp = self.display
        if disp is None:
            Log.w("CRMCController: Display instance not available.")
            return

        cust = self.currentCustomer
        if not cust:
            disp.clear()
            return

        if self._current_view_state == self.VIEW_CUSTOMER:
            disp.showCustomer(cust)

        elif self._current_view_state == self.VIEW_CONTACT:
            if cust.contacts and self._current_contact_index < len(cust.contacts):
                disp.showContact(cust.contacts[self._current_contact_index])
            else:
                disp.showCustomer(cust)

        elif self._current_view_state == self.VIEW_ACTIVITY:
            if cust.activities and self._current_activity_index < len(cust.activities):
                disp.showActivity(cust.activities[self._current_activity_index])
            else:
                disp.showCustomer(cust)

    # -------------------------------------------------------------------------
    # Button Callbacks & Interrupt Safety
    # -------------------------------------------------------------------------

    def buttonPressed(self, name):
        """
        Callback invoked by Button.py interrupt service routine.
        Applies software debouncing and schedules/flags processing outside the ISR.

        Parameters:
        ----------
        name : str
            Name of the button reporting the press event
        """
        now = time.ticks_ms() if hasattr(time, "ticks_ms") else int(time.time() * 1000)
        # 200ms debounce
        diff = (now - self._last_button_time) if hasattr(time, "ticks_diff") else (now - self._last_button_time)
        if hasattr(time, "ticks_diff"):
            diff = time.ticks_diff(now, self._last_button_time)

        if diff < 200:
            return

        self._last_button_time = now
        Log.i(f"CRMCController: Button '{name}' pressed (IRQ)")

        self._button_pending = True

        # Use micropython.schedule if available on hardware to execute outside ISR
        try:
            import micropython
            micropython.schedule(self._deferred_button_handler, 0)
        except Exception:
            # In testing environments or if schedule queue is full, process directly
            self.processPendingEvents()

    def buttonReleased(self, name):
        """Callback invoked by Button.py when the button is released."""
        pass

    def _deferred_button_handler(self, _):
        """Scheduled handler executed safely outside of the hardware ISR context."""
        self.processPendingEvents()

    def processPendingEvents(self):
        """Processes any queued button actions outside of the hardware ISR."""
        if self._button_pending:
            self._button_pending = False
            self.handleButton()

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _build_url(self, endpoint: str, customerID: int = None) -> str:
        """Constructs full absolute URL with optional customerID query parameter."""
        base = self._base_url
        if endpoint == "version":
            path = "/customer/version"
        elif endpoint == "get_customers":
            path = "/customer/get_customers"
        elif endpoint == "contacts":
            path = "/contacts"
        elif endpoint == "activities":
            path = "/activities"
        elif endpoint.startswith("/"):
            path = endpoint
        else:
            path = "/" + endpoint

        full_url = f"{base}{path}" if base else path

        if customerID is not None:
            sep = "&" if "?" in full_url else "?"
            full_url = f"{full_url}{sep}customerID={customerID}"

        return full_url

    def _fetch_json(self, url: str):
        """Safely queries Net.getJson and returns parsed payload."""
        net_instance = self.net
        if not net_instance or not hasattr(net_instance, "getJson"):
            Log.e(f"CRMCController: Net instance cannot fetch URL '{url}'")
            return None
        try:
            return net_instance.getJson(url)
        except Exception as e:
            Log.e(f"CRMCController: Error fetching '{url}': {e}")
            return None

    def _extract_list(self, raw_data, expected_key: str = None) -> list:
        """Extracts list of records from bare JSON lists or wrapped dict structures."""
        if raw_data is None:
            return []
        if isinstance(raw_data, list):
            return raw_data
        if isinstance(raw_data, dict):
            if expected_key and expected_key in raw_data and isinstance(raw_data[expected_key], list):
                return raw_data[expected_key]
            # Search for any list inside the dict
            for k, v in raw_data.items():
                if isinstance(v, list):
                    return v
        return []

    def _parse_customer(self, item) -> Customer:
        """Instantiates a Customer object from dict or Customer instance."""
        if isinstance(item, Customer):
            return item
        if isinstance(item, dict):
            cid = item.get("customerID") or item.get("customer_id") or item.get("id") or 0
            cname = item.get("customerName") or item.get("customer_name") or item.get("name") or "Unknown"
            return Customer(customerID=int(cid), customerName=str(cname))
        return None

    def _parse_contact(self, item, default_cid: int = 0) -> Contact:
        """Instantiates a Contact object from dict or Contact instance."""
        if isinstance(item, Contact):
            return item
        if isinstance(item, dict):
            cnt_id = item.get("contactID") or item.get("contact_id") or item.get("id") or 0
            cid = item.get("customerID") or item.get("customer_id") or default_cid
            cname = item.get("contactName") or item.get("contact_name") or item.get("name") or "Unknown"
            crole = item.get("contactRole") or item.get("contact_role") or item.get("role") or ""
            return Contact(contactID=int(cnt_id), customerID=int(cid), contactName=str(cname), contactRole=str(crole))
        return None

    def _parse_activity(self, item, default_cid: int = 0) -> Activity:
        """Instantiates an Activity object from dict or Activity instance."""
        if isinstance(item, Activity):
            return item
        if isinstance(item, dict):
            aid = item.get("activityID") or item.get("activity_id") or item.get("id") or 0
            cid = item.get("customerID") or item.get("customer_id") or default_cid
            atype = item.get("activityType") or item.get("activity_type") or item.get("type") or "Note"
            adate = item.get("activityDate") or item.get("activity_date") or item.get("date") or ""
            adesc = item.get("activityDescription") or item.get("activity_description") or item.get("description") or ""
            return Activity(activityID=int(aid), customerID=int(cid), activityType=str(atype), activityDate=str(adate), activityDescription=str(adesc))
        return None


# -----------------------------------------------------------------------------
# Self-Contained Test Execution Block
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    Log.i("Testing CRMCController with Mock Net, Mock Button, and Mock Display...")

    class MockNet:
        """Mock network adapter simulating REST API endpoints."""
        def __init__(self):
            self.connected = False
            self.ip = "192.168.1.150"

        def connect(self, ssid, password=None):
            self.connected = True
            Log.i(f"MockNet: Connected to {ssid}")

        def getLocalIp(self):
            return self.ip

        def getJson(self, url):
            Log.i(f"MockNet: GET request to '{url}'")
            if "/customer/version" in url:
                return {"version": "1.0.0"}
            elif "/customer/get_customers" in url:
                return [
                    {"customerID": 101, "customerName": "Wayne Enterprises"},
                    {"customerID": 102, "customerName": "Stark Industries"}
                ]
            elif "/contacts" in url:
                if "customerID=101" in url:
                    return [{"contactID": 1, "customerID": 101, "contactName": "Lucius Fox", "contactRole": "Director"}]
                elif "customerID=102" in url:
                    return [{"contactID": 2, "customerID": 102, "contactName": "Pepper Potts", "contactRole": "CEO"}]
                else:
                    # Return all contacts for Sequence A
                    return [
                        {"contactID": 1, "customerID": 101, "contactName": "Lucius Fox", "contactRole": "Director"},
                        {"contactID": 2, "customerID": 102, "contactName": "Pepper Potts", "contactRole": "CEO"}
                    ]
            elif "/activities" in url:
                if "customerID=101" in url:
                    return [{"activityID": 10, "customerID": 101, "activityType": "Call", "activityDate": "2026-11-18", "activityDescription": "Tech sync"}]
                elif "customerID=102" in url:
                    return [{"activityID": 11, "customerID": 102, "activityType": "Meeting", "activityDate": "2026-11-19", "activityDescription": "Budget review"}]
                else:
                    # Return all activities for Sequence A
                    return [
                        {"activityID": 10, "customerID": 101, "activityType": "Call", "activityDate": "2026-11-18", "activityDescription": "Tech sync"},
                        {"activityID": 11, "customerID": 102, "activityType": "Meeting", "activityDate": "2026-11-19", "activityDescription": "Budget review"}
                    ]
            return None

    class MockButton:
        def __init__(self):
            self.handler = None
            self.pressed = False

        def setHandler(self, handler):
            self.handler = handler

        def isPressed(self):
            return self.pressed

    class MockLCD:
        def __init__(self):
            self.lines = [" " * 16, " " * 16]

        def clear(self, line=-1):
            self.lines = [" " * 16, " " * 16]

        def reset(self):
            self.clear()

        def showText(self, text, row=0, col=0):
            current = list(self.lines[row])
            for i, ch in enumerate(text):
                if col + i < 16:
                    current[col + i] = ch
            self.lines[row] = "".join(current)

    from Display import Display
    mock_lcd = MockLCD()
    mock_display = Display(lcd=mock_lcd)

    # -------------------------------------------------------------------------
    # TEST 1: SEQUENCE A (Eager Loading)
    # -------------------------------------------------------------------------
    Log.i("--- STARTING TEST 1: Sequence A (Eager Loading) ---")
    mock_net_a = MockNet()
    mock_btn_a = MockButton()
    ctrl_a = CRMCController(
        net=mock_net_a,
        button=mock_btn_a,
        display=mock_display,
        base_url="http://mock-api.local",
        ssid="Test_WiFi",
        mode="A"
    )

    ctrl_a.start()
    assert len(ctrl_a.customers) == 2, "Expected 2 customers in Sequence A"
    assert len(ctrl_a.all_contacts) == 2, "Expected 2 pre-fetched contacts in Sequence A"
    assert len(ctrl_a.all_activities) == 2, "Expected 2 pre-fetched activities in Sequence A"
    assert mock_display.currentScreen == "CUSTOMER"
    assert "Cust #101" in mock_lcd.lines[0]
    Log.i("Sequence A startup verified.")

    # Test filtering for Customer 101
    f_contacts, f_activities = ctrl_a.filterNonClientData(101)
    assert len(f_contacts) == 1 and f_contacts[0].contactName == "Lucius Fox"
    assert len(f_activities) == 1 and f_activities[0].activityType == "Call"
    Log.i("Sequence A filterNonClientData verified.")

    # -------------------------------------------------------------------------
    # TEST 2: SEQUENCE B (Lazy Loading)
    # -------------------------------------------------------------------------
    Log.i("--- STARTING TEST 2: Sequence B (Lazy Loading) ---")
    mock_net_b = MockNet()
    mock_btn_b = MockButton()
    ctrl_b = CRMCController(
        net=mock_net_b,
        button=mock_btn_b,
        display=mock_display,
        base_url="http://mock-api.local",
        ssid="Test_WiFi",
        mode="B"
    )

    ctrl_b.start()
    assert len(ctrl_b.customers) == 2, "Expected 2 customers in Sequence B"
    assert len(ctrl_b.all_contacts) == 0, "Sequence B should not pre-fetch all contacts"
    assert len(ctrl_b.all_activities) == 0, "Sequence B should not pre-fetch all activities"
    assert mock_display.currentScreen == "CUSTOMER"
    Log.i("Sequence B startup verified.")

    # Verify on-demand loading for Customer 101
    ctrl_b.selectCustomer(101)
    cust101 = ctrl_b.currentCustomer
    assert len(cust101.contacts) == 1 and cust101.contacts[0].contactName == "Lucius Fox"
    assert len(cust101.activities) == 1 and cust101.activities[0].activityType == "Call"
    Log.i("Sequence B on-demand fetch verified.")

    # -------------------------------------------------------------------------
    # TEST 3: User Interaction & Button Rotation
    # -------------------------------------------------------------------------
    Log.i("--- STARTING TEST 3: Button Interaction & Display Rotation ---")
    # Current view: Customer 101
    assert mock_display.currentScreen == "CUSTOMER"
    assert "Cust #101" in mock_lcd.lines[0]

    # Press 1: Rotate to Contact
    ctrl_b.handleButton()
    assert mock_display.currentScreen == "CONTACT"
    assert "Lucius Fox" in mock_lcd.lines[0]

    # Press 2: Rotate to Activity
    ctrl_b.handleButton()
    assert mock_display.currentScreen == "ACTIVITY"
    assert "Call" in mock_lcd.lines[0]

    # Press 3: Advances to next Customer (102) and fetches on-demand
    ctrl_b.handleButton()
    assert ctrl_b.currentCustomer.customerID == 102
    assert mock_display.currentScreen == "CUSTOMER"
    assert "Cust #102" in mock_lcd.lines[0]
    Log.i("Button rotation across views and customers verified.")

    # Test interrupt-safe callback
    ctrl_b.buttonPressed("CRMC_Button")
    assert mock_display.currentScreen == "CONTACT"
    assert "Pepper Potts" in mock_lcd.lines[0]
    Log.i("Interrupt-safe buttonPressed callback verified.")

    Log.i("Testing complete - all checks passed")
