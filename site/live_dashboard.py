# site/live_dashboard.py
#
# Dashboard wrapper.
# Allows instruction files to start the dashboard without repeating WebServer setup.
#
# Usage in any instruction file:
#
#   import sys
#
#   if "/site" not in sys.path:
#       sys.path.append("/site")
#
#   from live_dashboard import start_live_dashboard
#
#   dashboard = start_live_dashboard(locals())
#
#   while True:
#       dashboard.update()
#       ...

try:
    from hosting import WebServer
except ImportError:
    import sys

    if "/site" not in sys.path:
        sys.path.append("/site")

    from hosting import WebServer


class LiveDashboard:
    def __init__(
        self,
        rgb_sensor=None,
        temperature=None,
        pumps=None,
        peltier=None,
        port=80,
        status_func=None
    ):
        self.rgb_sensor = rgb_sensor
        self.temperature = temperature
        self.pumps = pumps
        self.peltier = peltier
        self.port = port
        self.status_func = status_func

        self.server = None
        self.started = False

    def start(self):
        if self.started:
            return

        try:
            self.server = WebServer(
                port=self.port,
                rgb_sensor=self.rgb_sensor,
                temperature=self.temperature,
                pumps=self.pumps,
                peltier=self.peltier,
                status_func=self.status_func
            )

            self.server.start()
            self.started = True

            print("Live dashboard started on port", self.port)

        except Exception as error:
            self.server = None
            self.started = False

            print("Live dashboard failed to start:", error)

    def update(self):
        if not self.started:
            return

        if self.server is None:
            return

        try:
            self.server.update()

        except Exception as error:
            print("Live dashboard update error:", error)

    def stop(self):
        if self.server is not None:
            try:
                self.server.stop()
            except Exception as error:
                print("Live dashboard stop error:", error)

        self.server = None
        self.started = False

        print("Live dashboard stopped.")


def start_live_dashboard(objects=None, port=80):
    if objects is None:
        objects = {}

    dashboard = LiveDashboard(
        rgb_sensor=objects.get("rgb_sensor", None),
        temperature=objects.get("temperature", None),
        pumps=objects.get("pumps", None),
        peltier=objects.get("peltier", None),
        port=port
    )

    dashboard.start()
    return dashboard