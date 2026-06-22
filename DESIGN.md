## Important Design Decisions for this project

# Case 1: why trigger_session is separate from the Click commands that call it

**The Problem:**
Multiple functions need to use the trigger_session functionality as there are both `start` and `multi_start` commands. 

**Options to consider:**
- Have a single click function that is called whenever the function is needed 
- Separate the logic into a separate function that can be called by both commands. 

**What I chose and why:**
By separating out the function that both commands can call, this work is easier to test and there is no adding unnecessary click wiring. 


# Case 2: Why run_session_loop is a plain fuction versus a repeated Click invocation 

**The Problem:**
In order to allow for users to run multiple sessions in a row, I needed to add that functionality 

**Options to consider:**
- Call function `start` multiple times in a row withing `multi_start`
- Use a for loop calling helper functions that do not invoke more Click functions. 

**What I chose and why:**
I chose to use a for loop calling helper functions that do not invoke more Click functions. Click is designed to take in user input and commands from the terminal. Utilizing multiple calls to more click functions means that the Click context does not need to be created over again. Likewise, the point of click is to handle the wiring of input and output from the terminal. Instead, I can use that wiring once and focus on putting the core logic in regular python with a for loop and helper functions. 

## Case 3: Why `tick_interval=0` for testing instead of mocking `time.sleep`

**The Problem:**
In order to make testing easier without large intervals, there needs to be some way to allow for a 0 second interval for breaks and sessions. 

**Options to Consider:**
- Use `tick_interval=0` to allow for an interval with no time 
- Mocking`time.sleep` to allow for an interval with no time


**What I chose and why:**
Using `tick_interval=0` allowed for less of a refactor within the functionality of `countdown`. Likewise, it allows for testing manually on the command line. Using a mock would not allow the same functionality for manual testing. 

**What I'd do differently:**