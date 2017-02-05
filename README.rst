::
              __       __    __
    .--.--.--|__.-----|  |--|  |--.-----.-----.-----.
    |  |  |  |  |__ --|     |  _  |  _  |     |  -__|
    |________|__|_____|__|__|_____|_____|__|__|_____|
                                       version 2.3.2

    Build composable event pipeline servers with minimal effort.



    =====================
    wishbone.input.docker
    =====================

    Version: 1.0.0

    Consumes Docker container events and logs.
    ------------------------------------------


        Subscribes to the Docker runtime and consumes events and logs.

        Container logs have following format:

            {"log": "2017-02-05T12:22:13 wishbone[1]: error switch: Module has no queue three.", "container_name": "test"}

        Container events keep Docker's standard


        Parameters:

            - base_url(str)("unix://var/run/docker.sock")
               |  The Docker host

            - auto_follow(bool)(True)
               |  When True automatically starts to tail

        Queues:

            - events
               |  The Docker runtime events.

            - container_stdout
               |  The A description of the queue

