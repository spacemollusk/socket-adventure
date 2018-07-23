import socket


class Server(object):
    """
    An adventure game socket server
    
    An instance's methods share the following variables:
    
    * self.socket: a "bound" server socket, as produced by socket.bind()
    * self.client_connection: a "connection" socket as produced by socket.accept()
    * self.input_buffer: a string that has been read from the connected client and
      has yet to be acted upon.
    * self.output_buffer: a string that should be sent to the connected client; for
      testing purposes this string should NOT end in a newline character. When
      writing to the output_buffer, DON'T concatenate: just overwrite.
    * self.done: A boolean, False until the client is ready to disconnect
    * self.room: one of 0, 1, 2, 3. This signifies which "room" the client is in,
      according to the following map:
      
                                     3                      N
                                     |                      ^
                                 1 - 0 - 2                  |
                                 
    When a client connects, they are greeted with a welcome message. And then they can
    move through the connected rooms. For example, on connection:
    
    OK! Welcome to Realms of Venture! This room has brown wall paper!  (S)
    move north                                                         (C)
    OK! This room has white wallpaper.                                 (S)
    say Hello? Is anyone here?                                         (C)
    OK! You say, "Hello? Is anyone here?"                              (S)
    move south                                                         (C)
    OK! This room has brown wall paper!                                (S)
    move west                                                          (C)
    OK! This room has a green floor!                                   (S)
    quit                                                               (C)
    OK! Goodbye!                                                       (S)
    
    Note that we've annotated server and client messages with *(S)* and *(C)*, but
    these won't actually appear in server/client communication. Also, you'll be
    free to develop any room descriptions you like: the only requirement is that
    each room have a unique description.
    """

    game_name = "Realms of Venture"

    def __init__(self, port=50000):
        self.input_buffer = ""
        self.output_buffer = ""
        self.done = False
        self.socket = None
        self.client_connection = None
        self.port = port

        self.room = 0

        # I've chosen to implement the game map as an instance variable dict.
        # The keys are (current_room, direction_to_go) tuples, and their keys
        # are the resulting destinations.
        self.moves = {(0, 'north'):3,
                      (0, 'east'):2,
                      (0, 'west'):1,
                      (1, 'east'):0,
                      (2, 'west'):0,
                      (3, 'south'):0}

    def connect(self):
        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
            socket.IPPROTO_TCP)

        address = ('127.0.0.1', self.port)
        self.socket.bind(address)
        self.socket.listen(1)

        self.client_connection, address = self.socket.accept()

    def room_description(self, room_number):
        """
        For any room_number in 0, 1, 2, 3, return a string that "describes" that
        room.

        Ex: `self.room_number(1)` yields "Brown wallpaper covers the walls, bathing
        the room in warm light reflected from the half-drawn curtains."

        :param room_number: int
        :return: str
        """
        room_descs = ["You are in a large room with stone walls and a wooden door \
                      on the north, east, and west walls.",
                      "You enter a small storage room with shelves full of \
                      strange jars.",
                      "This room has fancy red wallpaper and a skylight in the \
                      ceiling.",
                      "There appears to be nothing in this room but a marble \
                      statue of a wizard."]
        try:
            return room_descs[room_number]
        except IndexError:
            return "Whoops, something went wrong with the room system."

    def greet(self):
        """
        Welcome a client to the game.
        
        Puts a welcome message and the description of the client's current room into
        the output buffer.
        
        :return: None 
        """
        self.output_buffer = "Welcome to {}! {}".format(
            self.game_name,
            self.room_description(self.room)
        )

    def get_input(self):
        """
        Retrieve input from the client_connection. All messages from the client
        should end in a newline character: '\n'.
        
        This is a BLOCKING call. It should not return until there is some input from
        the client to receive.
         
        :return: None 
        """
        received = b'\n'
        while b'\n' not in received:
            received += self.client_connection.recv(16)
        
        self.input_buffer = received.decode.strip()


    def move(self, argument):
        """
        Moves the client from one room to another.
        
        Examines the argument, which should be one of:
        
        * "north"
        * "south"
        * "east"
        * "west"
        
        "Moves" the client into a new room by adjusting self.room to reflect the
        number of the room that the client has moved into.
        
        Puts the room description (see `self.room_description`) for the new room
        into "self.output_buffer".
        
        Tries to update self.room to the value corresponding to the appropriate
        (current_room, direction) key in self.moves.

        Raises an error if the requested tuple is not in the key set; i.e.,
        the player has entered an illegal move.

        :param argument: str
        :return: None
        """
        
        try:
            self.room = self.moves[(self.room, argument)]
            self.output_buffer = self.room_description
        except KeyError:
            self.output_buffer = "You can't go that way from here!"

    def say(self, argument):
        """
        Lets the client speak by putting their utterance into the output buffer.
        
        For example:
        `self.say("Is there anybody here?")`
        would put
        `You say, "Is there anybody here?"`
        into the output buffer.
        
        :param argument: str
        :return: None
        """

        self.output_buffer += 'You say: "{}"'.format(argument)

    def quit(self, argument):
        """
        Quits the client from the server.
        
        Turns `self.done` to True and puts "Goodbye!" onto the output buffer.
        
        Ignore the argument.
        
        :param argument: str
        :return: None
        """

        self.output_buffer += "Goodbye!"
        self.push_output()
        self.done = True

    def route(self):
        """
        Examines `self.input_buffer` to perform the correct action (move, quit, or
        say) on behalf of the client.
        
        For example, if the input buffer contains "say Is anybody here?" then `route`
        should invoke `self.say("Is anybody here?")`. If the input buffer contains
        "move north", then `route` should invoke `self.move("north")`.
        
        :return: None
        """
        received = self.input_buffer.split(" ")

        command = received.pop(0)
        arguments = " ".join(received)

        { 'quit': self.quit,
          'move': self.move,
          'say': self.say
        }[command](arguments)

        if self.input_buffer.startswith("say "):
            say_arg = self.input_buffer[4:]
            self.say(say_arg)
        elif self.input_buffer.startswith("move "):
            move_arg = self.input_buffer[5:]
            self.move(move_arg)
        elif self.input_buffer == "quit":
            self.quit(None)
        pass

    def push_output(self):
        """
        Sends the contents of the output buffer to the client.
        
        This method should prepend "OK! " to the output and append "\n" before
        sending it.
        
        :return: None 
        """
        self.client_connection.sendall(b"OK! " + self.output_buffer.encode() + b"\n")

    def serve(self):
        self.connect()
        self.greet()
        self.push_output()

        while not self.done:
            self.get_input()
            self.route()
            self.push_output()

        self.client_connection.close()
        self.socket.close()
