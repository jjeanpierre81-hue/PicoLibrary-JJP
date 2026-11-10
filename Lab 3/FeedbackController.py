"""
A basic template file for using the Model class in PicoLibrary
This will allow you to implement simple Statemodels with some basic
event-based transitions.
"""

# Import whatever Library classes you need - StateModel is obviously needed
# Counters imported for Timer functionality, Button imported for button events
import time
import random
from Log import *
from StateModel import *
from Counters import *
from Displays import *
from Buzzer import *
from modelclasses import *

## You may want to remove any module you do not need from the imports below
from Button import *
from Lights import *
from Sensors import *

"""
This is the template for a Controller - you should rename this class to something
that is supported by your class diagram. This should associate with your other
classes, and any PicoLibrary classes. If you are using Buttons, you will implement
buttonPressed and buttonReleased.

To implement the state model, you will need to implement __init__ and 4 other methods
to support model start, stop, entry actions, exit actions, and state actions.

The following methods must be implemented:
__init__: create instances of your View and Business model classes, create an instance
of the StateModel with the necessary number of states and add the transitions, buttons
and timers that the StateModel needs

stateEntered(self, state, event) - Entry actions
stateLeft(self, state, event) - Exit actions
stateDo(self, state) - do Activities

# A couple other methods are available - but they can be left alone for most purposes

run(self) - runs the State Model - this will start at State 0 and drive the state model
stop(self) - stops the State Model - will stop processing events and stop the timers

This template currently implements a very simple state model that uses a button to
transition from state 0 to state 1 then a 5 second timer to go back to state 0.
"""
WELCOME = 0
FEEDBACK = 1
HAPPY = 2
SAD = 3
ALARM = 4
RESETTING = 5

class FeedbackController:

    def __init__(self):
        
        # STEP 1.
        # Instantiate whatever classes from your own model that you need to control
        # Handlers can now be set to None - we will add them to the model and it will
        # do the handling
        
        self._display = LCDDisplay(sda=0, scl=1)
        self._buzzer = PassiveBuzzer(pin=15, name='Buzzer')
        self._stats = FeedbackStats()
        self._alarmOn = False
        self._show_stats_on_welcome = False

        # Instantiate a Model. Needs to have the number of states, self as the handler
        # You can also say debug=True to see some of the transitions on the screen
        # Here is a sample for a model with 4 states
        self._model = StateModel(6, self, debug=True)
        
        # Instantiate any Buttons that you want to process events from and add
        # them to the model
        self._button1 = Button(17, 'happy', handler=None)
        self._button2 = Button(16, 'sad', handler=None)        
        self._model.addButton(self._button1)
        self._model.addButton(self._button2)
        
        # add other buttons if needed. Note that button names must be distinct
        # for all buttons. Events will come back with [buttonname]_press and
        # [buttonname]_release

        # ...
        
        # Instantiate any sensor you need to process their trip/untrip events from
        # Events from sensors come back as sensorname_trip and sensorname_untrip

        self._pir = DigitalSensor(pin=3, name="motion", lowActive=False, handler=None)
        self._model.addSensor(self._pir)

        # Add any timer you have. Multiple timers may be added but they must all
        # have distinct names. Events come back as [timername}_timeout
        self._timer = SoftwareTimer(name="timer", handler=None)
        self._model.addTimer(self._timer)

        # Add any custom events as appropriate for your state model. e.g.
        # self._model.addCustomEvent("collision_detected")
        self._model.addCustomEvent('feedbackBelowThreshold')

        # Now add all the transitions from your state model. Any custom events
        # must be defined above first. You can have a state transition to another
        # state based on multiple events - which is why the eventlist is an array
        # Syntax: self._model.addTransition( SOURCESTATE, [eventlist], DESTSTATE)
        
        # some examples:
        self._model.addTransition(WELCOME, ["motion_trip"], FEEDBACK)
        self._model.addTransition(FEEDBACK, ["timer_timeout"], WELCOME)

        self._model.addTransition(FEEDBACK, ["happy_press"], HAPPY)
        self._model.addTransition(FEEDBACK, ["sad_press"], SAD)

        self._model.addTransition(HAPPY, ["timer_timeout"], WELCOME)
        self._model.addTransition(SAD, ["timer_timeout"], WELCOME)

        self._model.addTransition(SAD, ["feedbackBelowThreshold"], ALARM)

        self._model.addTransition(ALARM, ["sad_press"], RESETTING)
        self._model.addTransition(RESETTING, ["timer_timeout"], WELCOME)
        self._model.addTransition(RESETTING, ["sad_release"], ALARM)

        # etc.
    
    def showWelcome(self):
        self._display.clear()
        pct = int(self._stats.getPercentage() * 100)

        if self._show_stats_on_welcome:
            self._display.showText('Today happy:', 0)       
            self._display.showText('{}%'.format(pct), 1)   
        else:
            greetings = [
                'Hello there!',
                'Welcome :)',
                'Hi, shopper!',
                'Nice to see you',
                'Tap to rate us',
                'Thanks for visit'
            ]
            greeting = random.choice(greetings)
            self._display.showText(greeting, 0)
            self._display.showText('Welcome to IKEA', 1)

        # flip for next time
        self._show_stats_on_welcome = not self._show_stats_on_welcome

        # update LEDs based on stats
        self._stats.showStats()


    def showPrompt(self):
        self._display.clear()
        prompts = [
        ('Did you enjoy',   'your visit?'),
        ('Rate your visit', '1 tap = 1 vote'),
        ('How was visit?',  'Green / Red'),
        ('Tap green',   'for happy'),
        ('Press red',   'if not happy')]
        line0, line1 = random.choice(prompts)
        self._display.clear()
        self._display.showText(line0, 0)
        self._display.showText(line1, 1)
    
    def happyAction(self):
        self._display.clear()
        happy_msgs = [
        ('Thanks for your', 'response! :)'),
        ('Thanks for your', 'feedback!'),
        ('So glad you are', 'happy today!'),
        ('You made our',    'day :)'),
        ('We love happy',   'customers!')
        ]
        line0, line1 = random.choice(happy_msgs)
        self._display.clear()
        self._display.showText(line0, 0)
        self._display.showText(line1, 1)
    
    def sadAction(self):
        self._display.clear()
        sad_msgs = [
        ('Sorry to hear',   'that :('),
        ('Thanks for your', 'honesty'),
        ('We will improve', 'this!'),
        ('Manager will',    'be alerted'),
        ('We will work on', 'this, promise')
        ]
        line0, line1 = random.choice(sad_msgs)
        self._display.clear()
        self._display.showText(line0, 0)
        self._display.showText(line1, 1)
    
    def displayAlarm(self):
        self._display.clear()
        self._display.showText('LOW SCORE!', 0)
        self._display.showText('Reset with red!', 1)

    def stateEntered(self, state, event):
        """
        stateEntered - is the handler for performing entry actions
        You get the state number of the state that just entered
        Make sure actions here are quick
        """
        
        # If statements to do whatever entry/actions you need for
        # for states that have entry actions
        Log.d(f'State {state} entered on event {event}')
        if state == WELCOME:
            # entry actions for state 0
            self._timer.cancel()
            self.showWelcome()
            self._timer.start(2)
        
        elif state == FEEDBACK:
            # entry actions for state 1
            self.showPrompt()
            self._timer.start(5)
        
        elif state == HAPPY:
            self.happyAction()
            self._stats.happy()
            self._buzzer.beep(tone=1000, duration=100)
            self._timer.start(4)

        elif state == SAD:
            self.sadAction()
            self._stats.sad()
            self._buzzer.beep(tone=300, duration=250)
            self._timer.start(4)

            if self._stats.getPercentage() < 0.3:
                self._model.processEvent("feedbackBelowThreshold")
        
            
        elif state == ALARM:
            self._alarmOn = True
            self.displayAlarm()

        elif state == RESETTING:
            self._display.clear()
            self._display.showText("HOLD TO RESET...", 0)
            # Start a 3-second timer
            self._timer.start(3)

    def stateLeft(self, state, event):
        """
        stateLeft - is the handler for performing exit/actions
        You get the state number of the state that just entered
        Make sure actions here are quick
        
        This is just like stateEntered, perform only exit/actions here
        """

        Log.d(f'State {state} exited on event {event}')
        if state == WELCOME: 
            self._timer.cancel()

        elif state == ALARM:
            self._alarmOn = False
            self._buzzer.stop()
        elif state == RESETTING:
             self._timer.cancel()
             if event == "timer_timeout":
                self._stats.reset()
        # etc.
    
    def stateEvent(self, state, event)->bool:
        """
        stateEvent - handler for performing actions for a specific event
        without leaving the current state. 
        Note that transitions take precedence over state events, so if you
        have a transition as well as an in-state action for the same event,
        the in-state action will never be called.

        This handler must return True if the event was processed, otherwise
        must return False.
        """
        
        # Recommend using the debug statement below ONLY if necessary - may
        # generate a lot of useless debug information.
        # Log.d(f'State {state} received event {event}')
        
        # Handle internal events here - if you need to do something
        if state == WELCOME and event == 'timer_timeout':
            self.showWelcome()        # this will alternate greeting/stats
            self._timer.start(2)      # restart 2s timer
            return True               # We handled this event
    
    # We did not handle any other in-state event
        return False

    def stateDo(self, state):
        """
        stateDo - the method that handles the do/actions for each state
        """
        
        # Now if you want to do different things for each state that has do actions
        if state == ALARM:
            # Remember you do not need to create a loop - the model takes care of that
            # For example, if you want a state to flash an LED, just turn it on and off
            # once, and the model will repeat it as long as you are in that state.
            self.playAlarmSound()

    def playAlarmSound(self):
        self._stats._lightstrip.setColor(RED, 8)
        self._buzzer.play(1200)
        time.sleep(0.25)
        self._stats._lightstrip.off()
        self._buzzer.play(900)
        time.sleep(0.25)

    def run(self):
        """
        Create a run() method - you can call it anything you want really, but
        this is what you will need to call from main.py or someplace to start
        the state model.
        """
        
        # The run method should simply do any initializations (if needed)
        # and then call the model's run method.
        # You can send a delay as a parameter if you want something other
        # than the default 0.1s. e.g.,  self._model.run(0.25)
        self._model.run()

    def stop(self):
        # The stop method should simply do any cleanup as needed
        # and then call the model's stop method.
        # This removes the button's handlers but will need to see
        # if the IRQ handlers should also be removed
        self._model.stop()
        

# Test your model. Note that this only runs the template class above
# If you are using a separate main.py or other control script,
# you will run your model from there.
if __name__ == '__main__':
    p = MyController()
    try:
        p.run()
    except KeyboardInterrupt:
        p.stop()    
