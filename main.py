#from control.instructions import test_instructions as module
#from control.instructions import pumpsTest as module
from control.instructions import fullLiveSystemTest as module
#from control.instructions import live_dashboard as module
#from control.instructions import fullTest as module

def main():
    print()
    print("====================================")
    print(" DB4 ESP32 SYSTEM START")
    print("====================================")

    if not hasattr(module, "startup"): raise Exception("Instruction module must define startup()")
    startup = getattr(module, 'startup')
    startup()


    print()
    print("Instruction module started.")


main()