class OptionNode:
    def __init__(self, text):
        self.text = text
        self.next = None

    def is_option(self):
        return True

class StoryNode:
    def __init__(self, text):
        self.text = text
        self.next = None
        self.options = []

    def add_option(self, option):
        self.options += [ option ]

    def is_option(self):
        return False

    def is_end(self):
        return self.next == None and len(self.options) == 0

    def has_options(self):
        return len(self.options) > 0


class Story:
    def __init__(self, name):
        self.name = name
        self.shown_options = False
        self.shown_end = False

    def load_story(self, inputs):
        """
        Inputs come in the format for an n by 3 array, where the first
        column is either STORY or OPTION, the second is always text
        and the third is either a number, empty or END, signifying the end
        of the story. The value of 3rd column will always be +2 of the index,
        so make sure to offset by this!
        """
        offset = -2
        nodes = []
        # You do not have to start with STORY
        for i in inputs:
            if i[0] == "":
                break
            elif i[0] == "OPTION":
                if len(nodes) == 0:
                    # We're starting on an option
                    nodes += [ StoryNode("Pick an option to start:") ]
                    offset += 1
                nodes += [ OptionNode(i[1]) ]
            elif i[0] == "STORY":
                nodes += [ StoryNode(i[1]) ]
            else:
                self.current_node = StoryNode("Could not load story")
                return

        # Now that we've created all the nodes so we can point at them, 
        # let's create the sequence
        lastNode = nodes[0]
        if len(nodes) > 1:
            nodes[0].next = nodes[1]
        for i in range(1, len(nodes)):
            input_index = i - 2 - offset
            if nodes[i].is_option():
                # Option nodes should not point to anything
                if lastNode.next == None:
                    lastNode.next = None
                lastNode.add_option(nodes[i])
                val = inputs[input_index][2]
                nodes[i].next = nodes[int(val)+offset]
            else:
                if len(inputs[input_index]) == 2:
                    nodes[i].next = nodes[i+1]
                elif inputs[input_index][2] != "END":
                    val = inputs[input_index][2]
                    nodes[i].next = nodes[int(val)+offset]
                lastNode = nodes[i]
        self.current_node = nodes[0]

    def can_step(self):
        return not (self.shown_options or self.shown_end)

    def do_step(self):
        text = [ self.current_node.text ]
        if self.current_node.has_options():
            text += [ "Use `%s value` to select an option"]
            val = 1
            for i in self.current_node.options:
                text += [ f"> {val}: {i.text}" ]
                val += 1
            self.shown_options = True
        elif self.current_node.is_end():
            text += [ "\n**The End**" ]
            self.shown_end = True
        else:
            self.current_node = self.current_node.next
            self.shown_options = False
        return text
    
    def choose(self, val):
        assert self.current_node.has_options()
        self.current_node = self.current_node.options[val].next
        self.shown_options = False
