
from machine import Pin
import time

from Display import Display
from CRMCController import CRMCController


# Simulated Customers API
class MockNet:

    def getLocalIp(self):
        return "192.168.1.150"

    def getJson(self, url):
        print("Mock API request:", url)

        if "/customer/version" in url:
            return {"version": "1.0.0"}

        if "/customer/get_customers" in url:
            return [
                {
                    "customerID": 101,
                    "customerName": "Wayne Enterprises"
                },
                {
                    "customerID": 102,
                    "customerName": "Stark Industries"
                }
            ]

        if "/contacts" in url:
            contacts = [
                {
                    "contactID": 1,
                    "customerID": 101,
                    "contactName": "Lucius Fox",
                    "contactRole": "Director"
                },
                {
                    "contactID": 2,
                    "customerID": 102,
                    "contactName": "Pepper Potts",
                    "contactRole": "CEO"
                }
            ]

            return self.filterData(url, contacts)

        if "/activities" in url:
            activities = [
                {
                    "activityID": 10,
                    "customerID": 101,
                    "activityType": "Call",
                    "activityDate": "2026-11-18",
                    "activityDescription": "Tech sync"
                },
                {
                    "activityID": 11,
                    "customerID": 102,
                    "activityType": "Meeting",
                    "activityDate": "2026-11-19",
                    "activityDescription": "Budget review"
                }
            ]

            return self.filterData(url, activities)

        return []

    def filterData(self, url, records):
        if "customerID=" not in url:
            return records

        customer_id = int(url.split("customerID=")[1].split("&")[0])

        return [
            item for item in records
            if item["customerID"] == customer_id
        ]


def main():

    # Choose "A" for eager loading
    # Choose "B" for lazy loading
    mode = "B"

    display = Display()
    net = MockNet()

    button = Pin(14, Pin.IN, Pin.PULL_UP)

    controller = CRMCController(
        net=net,
        display=display,
        base_url="http://mock-api.local",
        mode=mode,
        button_pin=14
    )

    # Load simulated customer data
    controller.start()

    print("CRMC System Started")
    print("Sequence:", mode)
    print("Press GP14 to navigate")

    last_button = button.value()

    while True:
        current_button = button.value()

        if last_button == 1 and current_button == 0:
            controller.handleButton()
            print("Button pressed")
            time.sleep_ms(200)

        last_button = current_button
        time.sleep_ms(20)


if __name__ == "__main__":
    main()

